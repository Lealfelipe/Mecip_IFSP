from django.shortcuts import render, redirect, get_object_or_404
from mecip.forms import QuestionnaireForm, QuestionnaireSectionForm, QuestionForm, QuestionAnswerOptionFormSet
from django.urls import reverse
from mecip.models import Questionnaire, QuestionnaireSection, Question
from django.contrib import messages
from mecip.permissions import access_required, can_manage_records


def is_admin(user):
    return can_manage_records(user)


def prepare_question_form(form, questionnaire):
    form.fields['section'].queryset = questionnaire.sections.all().order_by('order', 'name')
    return form


def prepare_section_form(form, questionnaire):
    form.fields['questionnaire'].initial = questionnaire
    form.fields['questionnaire'].disabled = True
    return form


# ========== QUESTIONARIO ==========

@access_required(is_admin)
def create_questionnaire(request):
    """Cria um novo questionario"""
    form_action = reverse('mecip:create_questionnaire')

    if request.method == 'POST':
        form = QuestionnaireForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Questionario'
        }

        if form.is_valid():
            questionnaire = form.save()
            messages.success(request, 'Questionario cadastrado com sucesso')
            return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire.pk)
        
        else:
            messages.error(request, 'Erro ao cadastrar questionario')

        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': QuestionnaireForm(),
        'form_action': form_action,
        'site_title': 'Criar Questionario'
    }
    return render(
        request,
        'mecip/create.html',
        context
    )


@access_required(is_admin)
def update_questionnaire(request, questionnaire_id):
    """Atualiza um questionario existente"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    form_action = reverse('mecip:update_questionnaire', args=(questionnaire_id,))

    if request.method == 'POST':
        form = QuestionnaireForm(request.POST, instance=questionnaire)

        if form.is_valid():
            form.save()
            messages.success(request, 'Questionario alterado com sucesso')
            return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire.id)

        else:
            messages.error(request, 'Erro ao alterar questionario')
            context = {
                'form': form,
                'form_action': form_action,
                'site_title': 'Editar Questionario',
            }

            return render(
                request,
                'mecip/create.html',
                context
            )

    form = QuestionnaireForm(instance=questionnaire)
    sections = questionnaire.sections.prefetch_related('questions', 'teams').order_by('order', 'name')
    
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar Questionario',
        'questionnaire': questionnaire,
        'sections': sections,
    }
    return render(request, 'mecip/update_questionnaire.html', context)


# ========== SECAO ==========

@access_required(is_admin)
def create_questionnaire_section(request, questionnaire_id):
    """Cria uma nova secao para um questionario"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    form_action = reverse('mecip:create_questionnaire_section', args=(questionnaire_id,))

    if request.method == 'POST':
        form = prepare_section_form(QuestionnaireSectionForm(request.POST), questionnaire)
        section = form.instance
        section.questionnaire = questionnaire

        if form.is_valid():
            section = form.save(commit=False)
            section.questionnaire = questionnaire
            section.save()
            form.save_m2m()
            messages.success(request, 'Secao cadastrada com sucesso')
            return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire_id)

        messages.error(request, 'Erro ao cadastrar secao')
    else:
        form = prepare_section_form(QuestionnaireSectionForm(), questionnaire)

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': f'Criar Secao - {questionnaire.name}',
        'questionnaire': questionnaire,
    }
    return render(request, 'mecip/create.html', context)


@access_required(is_admin)
def update_questionnaire_section(request, questionnaire_id, section_id):
    """Atualiza uma secao existente"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    section = get_object_or_404(QuestionnaireSection, pk=section_id, questionnaire=questionnaire)
    form_action = reverse('mecip:update_questionnaire_section', args=(questionnaire_id, section_id))

    if request.method == 'POST':
        form = prepare_section_form(QuestionnaireSectionForm(request.POST, instance=section), questionnaire)

        if form.is_valid():
            section = form.save(commit=False)
            section.questionnaire = questionnaire
            section.save()
            form.save_m2m()
            messages.success(request, 'Secao alterada com sucesso')
            return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire_id)

        messages.error(request, 'Erro ao alterar secao')
    else:
        form = prepare_section_form(QuestionnaireSectionForm(instance=section), questionnaire)

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': f'Editar Secao - {questionnaire.name}',
        'questionnaire': questionnaire,
        'section': section,
    }
    return render(request, 'mecip/create.html', context)


@access_required(is_admin)
def delete_questionnaire_section(request, questionnaire_id, section_id):
    """Deleta uma secao"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    section = get_object_or_404(QuestionnaireSection, pk=section_id, questionnaire=questionnaire)
    section.delete()
    messages.success(request, 'Secao deletada com sucesso')
    return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire_id)


# ========== QUESTAO ==========

@access_required(is_admin)
def create_question(request, questionnaire_id):
    """Cria uma nova questao para um questionario"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    form_action = reverse('mecip:create_question', args=(questionnaire_id,))

    if request.method == 'POST':
        form = prepare_question_form(QuestionForm(request.POST, request.FILES), questionnaire)
        question = form.instance
        answer_option_formset = QuestionAnswerOptionFormSet(
            request.POST,
            instance=question,
            prefix='answer_options',
        )
        context = {
            'form': form,
            'answer_option_formset': answer_option_formset,
            'form_action': form_action,
            'site_title': f'Criar Questao - {questionnaire.name}',
            'questionnaire': questionnaire,
        }

        if form.is_valid() and answer_option_formset.is_valid():
            question = form.save(commit=False)
            question.save()
            answer_option_formset.instance = question
            answer_option_formset.save()
            messages.success(request, 'Questao cadastrada com sucesso')
            return redirect('mecip:update_question', questionnaire_id=questionnaire_id, question_id=question.pk)
        
        else:
            messages.error(request, 'Erro ao cadastrar questao')

        return render(
            request,
            'mecip/create_question.html',
            context
        )

    form = prepare_question_form(QuestionForm(), questionnaire)
    answer_option_formset = QuestionAnswerOptionFormSet(prefix='answer_options')
    
    context = {
        'form': form,
        'answer_option_formset': answer_option_formset,
        'form_action': form_action,
        'site_title': f'Criar Questao - {questionnaire.name}',
        'questionnaire': questionnaire,
    }
    return render(
        request,
        'mecip/create_question.html',
        context
    )


@access_required(is_admin)
def update_question(request, questionnaire_id, question_id):
    """Atualiza uma questao existente"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    question = get_object_or_404(Question, pk=question_id, section__questionnaire=questionnaire)
    form_action = reverse('mecip:update_question', args=(questionnaire_id, question_id))

    if request.method == 'POST':
        form = prepare_question_form(QuestionForm(request.POST, request.FILES, instance=question), questionnaire)
        answer_option_formset = QuestionAnswerOptionFormSet(
            request.POST,
            instance=question,
            prefix='answer_options',
        )
        if form.is_valid() and answer_option_formset.is_valid():
            form.save()
            answer_option_formset.save()
            messages.success(request, 'Questao alterada com sucesso')
            return redirect('mecip:update_question', questionnaire_id=questionnaire_id, question_id=question.id)

        else:
            messages.error(request, 'Erro ao alterar questao')
            context = {
                'form': form,
                'answer_option_formset': answer_option_formset,
                'form_action': form_action,
                'site_title': f'Editar Questao - {questionnaire.name}',
                'questionnaire': questionnaire,
                'question': question,
            }

            return render(
                request,
                'mecip/create_question.html',
                context
            )

    form = prepare_question_form(QuestionForm(instance=question), questionnaire)
    answer_option_formset = QuestionAnswerOptionFormSet(instance=question, prefix='answer_options')
    
    context = {
        'form': form,
        'answer_option_formset': answer_option_formset,
        'form_action': form_action,
        'site_title': f'Editar Questao - {questionnaire.name}',
        'questionnaire': questionnaire,
        'question': question,
    }
    return render(request, 'mecip/create_question.html', context)


@access_required(is_admin)
def delete_question(request, questionnaire_id, question_id):
    """Deleta uma questao"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    question = get_object_or_404(Question, pk=question_id, section__questionnaire=questionnaire)
    
    question.delete()
    messages.success(request, 'Questao deletada com sucesso')
    return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire_id)
