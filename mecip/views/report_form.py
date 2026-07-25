from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Q
from mecip.forms import ReportForm, ReportQuestionAnswerForm, AttachmentFormSet
from django.urls import reverse
from mecip.models import Report, Course, Campus, Question, ReportQuestionAnswer, Type_Course, QuestionAnswerOption, ReferenceAttachment, Attachments
from django.contrib import messages
from django.http import JsonResponse
from mecip.permissions import access_required, can_answer_report, can_manage_records, can_view_report_questionnaire

@access_required(can_manage_records)
def create_report(request):
    form_action = reverse('mecip:create_report')

    if request.method == 'POST':
        form = ReportForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Relatorio',
        }

        if form.is_valid():
            report = form.save()
            _ensure_report_answers(report)
            messages.success(request, 'Relatorio criado com sucesso!')
            return redirect('mecip:update_report', report_id=report.pk)

        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': ReportForm(),
        'form_action': form_action,
        'site_title': 'Criar Relatorio',
    }
    return render(
        request,
        'mecip/create.html',
        context
    )

@access_required(can_manage_records)
def create_report_params(request, course_id, campus_id):
    course = get_object_or_404(Course, pk=course_id)
    campus = get_object_or_404(Campus, pk=campus_id)
    form_action = reverse('mecip:create_report_params', args=[course_id, campus_id])

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save()
            messages.success(request, "Relatorio criado com sucesso!")
            return redirect('mecip:update_report', report_id=report.pk)
    else:
        initial_data = {'type_course': course.type_course, 'campus': campus}
        form = ReportForm(initial=initial_data)

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Criar Relatorio',
    }
    return render(request, 'mecip/create.html', context)


@access_required(can_manage_records)
def update_report(request, report_id):
    report = get_object_or_404(Report, pk= report_id)
    form_action = reverse('mecip:update_report', args=(report_id,))

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)

        if form.is_valid():
            report = form.save()
            _ensure_report_answers(report)
            messages.success(request, 'Relatorio alterado com sucesso!')

            return redirect('mecip:update_report', report_id=report.id)

        else:
            messages.error(
                request,
                'Erro ao alterar o relatorio. Verifique se ja existe um '
                'relatorio para o mesmo curso, campus e ano.'
            )

            context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Editar Relatorio',
            }


            return render(
                request,
                'mecip/create.html',
                context
            )

    form = ReportForm(instance=report)
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar Relatorio',
    }
    return render(request, 'mecip/create.html', context)


def answer_questionnaire(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Voce precisa estar logado para responder o questionario.')
        return redirect('mecip:report', report_id=report_id)

    if not can_answer_report(request.user, report):
        messages.error(request, 'Somente usuario da equipe atribuida ou coordenador pode responder o questionario.')
        return redirect('mecip:report', report_id=report_id)

    if report.questionnaire is None:
        messages.error(request, 'Este relatorio nao tem questionario associado.')
        return redirect('mecip:report', report_id=report_id)

    _ensure_report_answers(report)
    report_questions = _get_report_questions(report)
    answers = ReportQuestionAnswer.objects.filter(report=report, question__in=report_questions).select_related(
        'question',
        'question__section',
        'selected_answer_option',
    ).prefetch_related(
        'question__answer_options',
        Prefetch(
            'attachments',
            queryset=Attachments.objects.select_related('reference_attachment'),
        ),
    ).order_by('question__section__order', 'question__order')
    answers_list = list(answers)
    total_questions = len(answers_list)
    current_index = int(request.GET.get('pergunta', 1) or 1)
    current_index = max(1, min(current_index, total_questions or 1))
    current_answer = answers_list[current_index - 1] if total_questions else None
    reference_attachments = ReferenceAttachment.objects.filter(active=True).order_by('name')
    question_steps = [
        {
            'number': index + 1,
            'title': answer.question.indicator or f'Pergunta {index + 1}',
            'is_current': index + 1 == current_index,
            'is_completed': bool(answer.answer and answer.answer.strip()),
        }
        for index, answer in enumerate(answers_list)
    ]

    if request.method == 'POST':
        if current_answer is None:
            messages.error(request, 'Nenhuma pergunta encontrada.')
            return redirect('mecip:view_questionnaire', report_id=report_id)

        option_id = request.POST.get(f'answer_option_{current_answer.id}')

        if option_id:
            option = get_object_or_404(QuestionAnswerOption, pk=option_id, question=current_answer.question)
            current_answer.selected_answer_option = option
            current_answer.answer = option.answer_value
        else:
            current_answer.selected_answer_option = None
            current_answer.answer = request.POST.get(f'answer_{current_answer.id}', '').strip()

        current_answer.free_text = request.POST.get(f'free_text_{current_answer.id}', '').strip()
        current_answer.save()

        attachment_formset = AttachmentFormSet(
            request.POST,
            request.FILES,
            instance=current_answer,
            prefix=f'attachments_{current_answer.id}',
        )
        selected_reference_attachment_ids = request.POST.getlist('selected_reference_attachments')

        if attachment_formset.is_valid():
            attachment_formset.save()
            if selected_reference_attachment_ids:
                selected_reference_attachments = ReferenceAttachment.objects.filter(
                    id__in=selected_reference_attachment_ids,
                    active=True,
                )
                for reference_attachment in selected_reference_attachments:
                    Attachments.objects.get_or_create(
                        answer=current_answer,
                        reference_attachment=reference_attachment,
                        defaults={
                            'name': reference_attachment.name,
                            'description': reference_attachment.description,
                        },
                    )
        else:
            context = {
                'report': report,
                'answer': current_answer,
                'attachment_formset': attachment_formset,
                'reference_attachments': reference_attachments,
                'current_index': current_index,
                'total_questions': total_questions,
                'previous_index': current_index - 1,
                'next_index': current_index + 1,
                'has_previous': current_index > 1,
                'has_next': current_index < total_questions,
                'question_steps': question_steps,
                'site_title': 'Responder Questionario',
            }
            messages.error(request, 'Erro ao salvar anexos.')
            return render(request, 'mecip/answer_questionnaire.html', context)

        action = request.POST.get('action')
        navigate_to = request.POST.get('navigate_to')

        if action == 'save_current':
            messages.success(request, 'Resposta salva com sucesso.')
            return redirect(f'{reverse("mecip:answer_questionnaire", args=(report_id,))}?pergunta={current_index}')

        if action == 'save_and_exit':
            messages.success(request, 'Resposta salva com sucesso.')
            return redirect('mecip:view_questionnaire', report_id=report_id)

        if navigate_to:
            return redirect(f'{reverse("mecip:answer_questionnaire", args=(report_id,))}?pergunta={navigate_to}')

        messages.success(request, 'Resposta salva com sucesso.')
        return redirect('mecip:view_questionnaire', report_id=report_id)

    attachment_formset = (
        AttachmentFormSet(instance=current_answer, prefix=f'attachments_{current_answer.id}')
        if current_answer
        else None
    )

    context = {
        'report': report,
        'answer': current_answer,
        'attachment_formset': attachment_formset,
        'reference_attachments': reference_attachments,
        'current_index': current_index,
        'total_questions': total_questions,
        'previous_index': current_index - 1,
        'next_index': current_index + 1,
        'has_previous': current_index > 1,
        'has_next': current_index < total_questions,
        'question_steps': question_steps,
        'site_title': 'Responder Questionario',
    }
    return render(request, 'mecip/answer_questionnaire.html', context)


def view_questionnaire(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Voce precisa estar logado para ver o questionario.')
        return redirect('mecip:report', report_id=report_id)

    if not can_view_report_questionnaire(request.user, report):
        messages.error(request, 'Somente membro da equipe atribuida ou coordenador pode ver o questionario.')
        return redirect('mecip:report', report_id=report_id)

    if report.questionnaire is None:
        messages.error(request, 'Este relatorio nao tem questionario associado.')
        return redirect('mecip:report', report_id=report_id)

    _ensure_report_answers(report)
    report_questions = _get_report_questions(report)
    answers = ReportQuestionAnswer.objects.filter(report=report, question__in=report_questions).select_related(
        'question',
        'question__section',
        'selected_answer_option',
    ).prefetch_related(
        Prefetch(
            'attachments',
            queryset=Attachments.objects.select_related('reference_attachment'),
        ),
    ).order_by('question__section__order', 'question__order')

    can_answer = can_answer_report(request.user, report)
    status_to_respond = report.status == "Em andamento" or report.status == "Pendente ajuste"

    # Verificar se todas as questoes tem resposta
    all_answered = len(answers) == report_questions.count() and all(a.answer and a.answer.strip() for a in answers)

    context = {
        'report': report,
        'answers': answers,
        'can_answer': can_answer,
        'status_to_respond': status_to_respond,
        'all_answered': all_answered,
        'site_title': 'Ver Questionario',
    }
    return render(request, 'mecip/view_questionnaire.html', context)


def advance_report_status(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Voce precisa estar logado para avancar o status do relatorio.')
        return redirect('mecip:report', report_id=report_id)

    if not can_answer_report(request.user, report):
        messages.error(request, 'Somente membro da equipe atribuida ou coordenador pode avancar o status.')
        return redirect('mecip:report', report_id=report_id)

    # Verificar se todas as respostas estao preenchidas
    report_questions = _get_report_questions(report)
    answers = ReportQuestionAnswer.objects.filter(report=report, question__in=report_questions)
    if len(answers) != report_questions.count() or not all(a.answer and a.answer.strip() for a in answers):
        messages.error(request, 'Todas as questoes devem ter resposta antes de avancar o status.')
        return redirect('mecip:view_questionnaire', report_id=report_id)

    # Avancar status para "Pendente avaliacao"
    report.status = "Pendente avaliação"
    report.save()
    messages.success(request, 'Status do relatorio avancado para "Pendente avaliacao".')

    return redirect('mecip:view_questionnaire', report_id=report_id)


def change_report_status(request, report_id, action):
    report = get_object_or_404(Report, pk=report_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Voce precisa estar logado para alterar o status do relatorio.')
        return redirect('mecip:view_questionnaire', report_id=report_id)

    if not can_manage_records(request.user):
        messages.error(request, 'Apenas coordenadores ou super administradores podem alterar o status do relatorio.')
        return redirect('mecip:view_questionnaire', report_id=report_id)

    allowed_actions = {
        'aprovar': 'Aprovado',
        'bloquear': 'Bloqueado',
        'ajustar': 'Pendente ajuste',
        'reprovar': 'Reprovado',
    }

    if action not in allowed_actions:
        messages.error(request, 'Acao de status invalida.')
        return redirect('mecip:view_questionnaire', report_id=report_id)

    report_questions = _get_report_questions(report)
    answers = ReportQuestionAnswer.objects.filter(report=report, question__in=report_questions)
    all_answered = len(answers) == report_questions.count() and all(a.answer and a.answer.strip() for a in answers)
    if not all_answered:
        messages.error(request, 'Todas as questoes devem ter resposta antes de alterar o status.')
        return redirect('mecip:view_questionnaire', report_id=report_id)

    report.status = allowed_actions[action]
    report.save()
    messages.success(request, f'Status do relatorio alterado para "{allowed_actions[action]}".')

    return redirect('mecip:view_questionnaire', report_id=report_id)


def _get_report_questions(report: Report):
    if report.questionnaire is None:
        return Question.objects.none()

    questions = Question.objects.filter(section__questionnaire=report.questionnaire)
    if report.assigned_team:
        questions = questions.filter(
            Q(section__teams=report.assigned_team) |
            Q(section__teams__isnull=True)
        )

    return questions.select_related('section').distinct().order_by('section__order', 'order')


def _ensure_report_answers(report: Report):
    if report.questionnaire is None:
        return

    questions = _get_report_questions(report)
    for question in questions:
        ReportQuestionAnswer.objects.get_or_create(report=report, question=question)


def get_campus_for_course(request, course_id):
    type_course = get_object_or_404(Type_Course, pk=course_id)
    campuses = Campus.objects.filter(
        id__in=Course.objects.filter(type_course=type_course).values_list('campus', flat=True)
    ).distinct()
    data = [{'id': c.id, 'name': str(c)} for c in campuses]
    return JsonResponse(data, safe=False)


def get_courses_for_campus(request, campus_id):
    campus = get_object_or_404(Campus, pk=campus_id)
    type_courses = Type_Course.objects.filter(nome_curso__campus=campus).distinct()
    data = [{'id': c.id, 'name': c.type_name_course} for c in type_courses]
    return JsonResponse(data, safe=False)
