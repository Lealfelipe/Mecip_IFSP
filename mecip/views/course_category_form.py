from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from mecip.forms import CourseCategoryForm
from mecip.permissions import access_required, can_manage_records


@access_required(can_manage_records)
@require_http_methods(['GET', 'POST'])
def create_course_category(request):
    form = CourseCategoryForm(
        request.POST if request.method == 'POST' else None
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria de curso cadastrada com sucesso!')
            return redirect('mecip:create_course_category')
        messages.error(request, 'Corrija os erros abaixo para cadastrar a categoria.')

    return render(request, 'mecip/create.html', {
        'form': form,
        'form_action': reverse('mecip:create_course_category'),
        'site_title': 'Criar Categoria de Curso',
    })
