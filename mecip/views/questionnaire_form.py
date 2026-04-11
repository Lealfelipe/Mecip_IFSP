from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import QuestionnaireForm, QuestionForm
from django.urls import reverse
from mecip.models import Questionnaire, Question
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages


def is_admin(user):
    return user.is_superuser


# ========== QUESTIONÁRIO ==========

@user_passes_test(is_admin)
def create_questionnaire(request):
    """Cria um novo questionário"""
    form_action = reverse('mecip:create_questionnaire')

    if request.method == 'POST':
        form = QuestionnaireForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Questionário'
        }

        if form.is_valid():
            questionnaire = form.save()
            messages.success(request, 'Questionário cadastrado com sucesso')
            return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire.pk)
        
        else:
            messages.error(request, 'Erro ao cadastrar questionário')

        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': QuestionnaireForm(),
        'form_action': form_action,
        'site_title': 'Criar Questionário'
    }
    return render(
        request,
        'mecip/create.html',
        context
    )


@user_passes_test(is_admin)
def update_questionnaire(request, questionnaire_id):
    """Atualiza um questionário existente"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    form_action = reverse('mecip:update_questionnaire', args=(questionnaire_id,))

    if request.method == 'POST':
        form = QuestionnaireForm(request.POST, instance=questionnaire)

        if form.is_valid():
            form.save()
            messages.success(request, 'Questionário alterado com sucesso')
            return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire.id)

        else:
            messages.error(request, 'Erro ao alterar questionário')
            context = {
                'form': form,
                'form_action': form_action,
                'site_title': 'Editar Questionário',
            }

            return render(
                request,
                'mecip/create.html',
                context
            )

    form = QuestionnaireForm(instance=questionnaire)
    questions = Question.objects.filter(questionnaire=questionnaire).order_by('order')
    
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar Questionário',
        'questionnaire': questionnaire,
        'questions': questions,
    }
    return render(request, 'mecip/update_questionnaire.html', context)


# ========== QUESTÃO ==========

@user_passes_test(is_admin)
def create_question(request, questionnaire_id):
    """Cria uma nova questão para um questionário"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    form_action = reverse('mecip:create_question', args=(questionnaire_id,))

    if request.method == 'POST':
        form = QuestionForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': f'Criar Questão - {questionnaire.name}',
            'questionnaire': questionnaire,
        }

        if form.is_valid():
            question = form.save()
            messages.success(request, 'Questão cadastrada com sucesso')
            return redirect('mecip:update_question', questionnaire_id=questionnaire_id, question_id=question.pk)
        
        else:
            messages.error(request, 'Erro ao cadastrar questão')

        return render(
            request,
            'mecip/create_question.html',
            context
        )

    form = QuestionForm()
    # Pré-seleciona o questionário
    form.fields['questionnaire'].initial = questionnaire
    form.fields['questionnaire'].disabled = True
    
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': f'Criar Questão - {questionnaire.name}',
        'questionnaire': questionnaire,
    }
    return render(
        request,
        'mecip/create_question.html',
        context
    )


@user_passes_test(is_admin)
def update_question(request, questionnaire_id, question_id):
    """Atualiza uma questão existente"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    question = get_object_or_404(Question, pk=question_id, questionnaire=questionnaire)
    form_action = reverse('mecip:update_question', args=(questionnaire_id, question_id))

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)

        if form.is_valid():
            form.save()
            messages.success(request, 'Questão alterada com sucesso')
            return redirect('mecip:update_question', questionnaire_id=questionnaire_id, question_id=question.id)

        else:
            messages.error(request, 'Erro ao alterar questão')
            context = {
                'form': form,
                'form_action': form_action,
                'site_title': f'Editar Questão - {questionnaire.name}',
                'questionnaire': questionnaire,
                'question': question,
            }

            return render(
                request,
                'mecip/create_question.html',
                context
            )

    form = QuestionForm(instance=question)
    # Pré-seleciona o questionário
    form.fields['questionnaire'].initial = questionnaire
    form.fields['questionnaire'].disabled = True
    
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': f'Editar Questão - {questionnaire.name}',
        'questionnaire': questionnaire,
        'question': question,
    }
    return render(request, 'mecip/create_question.html', context)


@user_passes_test(is_admin)
def delete_question(request, questionnaire_id, question_id):
    """Deleta uma questão"""
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    question = get_object_or_404(Question, pk=question_id, questionnaire=questionnaire)
    
    question.delete()
    messages.success(request, 'Questão deletada com sucesso')
    return redirect('mecip:update_questionnaire', questionnaire_id=questionnaire_id)
