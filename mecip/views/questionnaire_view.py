from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from mecip.models import Questionnaire


def index_questionnaire(request):
    """Lista todos os questionários com paginação"""
    questionnaires = Questionnaire.objects \
        .order_by('-created_date')
    paginator = Paginator(questionnaires, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'site_title': 'Questionários'
    }

    return render(
        request,
        'mecip/index_questionnaire.html',
        context,
    )


def questionnaire(request, questionnaire_id):
    """Visualiza um questionário e suas questões"""
    questionnaire = get_object_or_404(
        Questionnaire, pk=questionnaire_id,
    )
    sections = questionnaire.sections.prefetch_related('questions', 'teams').order_by('order', 'name')

    context = {
        'questionnaire': questionnaire,
        'sections': sections,
        'site_title': f'Questionário - {questionnaire.name}',
    }

    return render(
        request,
        'mecip/questionnaire.html',
        context,
    )
