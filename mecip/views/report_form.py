from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import ReportForm, ReportQuestionAnswerForm
from django.urls import reverse
from mecip.models import Report, Course, Campus, Question, ReportQuestionAnswer
from django.contrib import messages

# from django.contrib.auth.decorators import user_passes_test

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
            course = form.cleaned_data['course']
            campus = form.cleaned_data['campus']

            curso_exists = Course.objects.filter(type_course=course.type_course, campus=campus).exists()

            if not curso_exists:
                messages.error(request, 'Curso não disponível nesse Campus')
            else:
                if Report.objects.filter(course=course, campus=campus).exists():
                    messages.error(request, 'Já existe um relatório para este curso neste campus.')
                else:
                    report = form.save()
                    _ensure_report_answers(report)
                    messages.success(request, 'Relatório criado com sucesso!')
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

def create_report_params(request, course_id, campus_id):
    course = get_object_or_404(Course, pk=course_id)
    campus = get_object_or_404(Campus, pk=campus_id)
    form_action = reverse('mecip:create_report_params', args=[course_id, campus_id])

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save(commit=False)
            if report.course != course or report.campus != campus:
                messages.error(request, "Não é possível criar o relatório")
            
            else:
                report.course = course  
                report.campus = campus
                report.save()
                messages.success(request, "Relatório criado com sucesso!")
                return redirect('mecip:update_report', report_id=report.pk)
    else:
        initial_data = {'course': course, 'campus': course.campus}
        form = ReportForm(initial=initial_data)

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Criar Relatório',
    }
    return render(request, 'mecip/create.html', context)


def update_report(request, report_id):
    report = get_object_or_404(Report, pk= report_id)
    form_action = reverse('mecip:update_report', args=(report_id,))

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)

        if form.is_valid():
            report = form.save()
            _ensure_report_answers(report)
            messages.success(request, 'Relatório alterado com sucesso!')

            return redirect('mecip:update_report', report_id=report.id)

        else:
            messages.error(request, 'Erro ao alterar o relatório. Já existe um relatório para o curso e campus.')

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
        messages.error(request, 'Você precisa estar logado para responder o questionário.')
        return redirect('mecip:report', report_id=report_id)

    if report.assigned_user and report.assigned_user != request.user and not request.user.is_superuser:
        messages.error(request, 'Apenas o usuário atribuído pode responder o questionário.')
        return redirect('mecip:report', report_id=report_id)

    if report.assigned_user is None and not request.user.is_superuser:
        messages.error(request, 'Relatório ainda não foi atribuído a um usuário. Só o usuário atribuído pode responder.')
        return redirect('mecip:report', report_id=report_id)

    if report.questionnaire is None:
        messages.error(request, 'Este relatório não tem questionário associado.')
        return redirect('mecip:report', report_id=report_id)

    answers = ReportQuestionAnswer.objects.filter(report=report).select_related('question')

    if request.method == 'POST':
        for answer_obj in answers:
            value = request.POST.get(f'answer_{answer_obj.id}', '').strip()
            answer_obj.answer = value
            answer_obj.save()

        messages.success(request, 'Respostas salvas com sucesso.')
        return redirect('mecip:report', report_id=report_id)

    context = {
        'report': report,
        'answers': answers,
        'site_title': 'Responder Questionário',
    }
    return render(request, 'mecip/answer_questionnaire.html', context)


def view_questionnaire(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado para ver o questionário.')
        return redirect('mecip:report', report_id=report_id)

    if not request.user.is_superuser:
        if report.assigned_team is None:
            messages.error(request, 'Relatório não tem equipe atribuída para visualização do questionário.')
            return redirect('mecip:report', report_id=report_id)

        if not report.assigned_team.users.filter(pk=request.user.pk).exists():
            messages.error(request, 'Somente membro da equipe atribuída pode ver o questionário.')
            return redirect('mecip:report', report_id=report_id)

    if report.questionnaire is None:
        messages.error(request, 'Este relatório não tem questionário associado.')
        return redirect('mecip:report', report_id=report_id)

    answers = ReportQuestionAnswer.objects.filter(report=report).select_related('question')

    can_answer = request.user.is_superuser or (report.assigned_user is not None and report.assigned_user == request.user)

    context = {
        'report': report,
        'answers': answers,
        'can_answer': can_answer,
        'site_title': 'Ver Questionário',
    }
    return render(request, 'mecip/view_questionnaire.html', context)


def _ensure_report_answers(report: Report):
    if report.questionnaire is None:
        return

    questions = Question.objects.filter(questionnaire=report.questionnaire)
    for question in questions:
        ReportQuestionAnswer.objects.get_or_create(report=report, question=question)
