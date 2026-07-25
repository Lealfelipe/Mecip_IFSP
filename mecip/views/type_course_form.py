from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import TypeCourseForm
from django.urls import reverse
from mecip.models import Type_Course
from django.contrib import messages
from mecip.permissions import access_required, can_manage_records

def is_admin(user):
    return can_manage_records(user)

@access_required(is_admin)
def create_type_course(request):
    form_action = reverse('mecip:create_type')

    if request.method == 'POST':
        form = TypeCourseForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Tipo de Curso'
        }

        if form.is_valid():
            type_course = form.save()
            messages.success(request, 'Curso cadastrado com sucesso')
            return redirect('mecip:update_type', type_course_id= type_course.pk)
        
        else:
            messages.error(request, 'Erro ao cadastrar curso')


        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': TypeCourseForm(),
        'form_action': form_action,
        'site_title': 'Criar Tipo de Curso'
    }
    return render(
        request,
        'mecip/create.html',
        context
    )

@access_required(is_admin)
def update_type_course(request, type_course_id):
    type_course = get_object_or_404(Type_Course, pk= type_course_id)
    form_action = reverse('mecip:update_type', args=(type_course_id,))

    if request.method == 'POST':
        form = TypeCourseForm(request.POST, instance=type_course)

        

        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo alterado com sucesso')
            return redirect('mecip:update_type', type_course_id=type_course.id)

        else:
            messages.error(request, 'Erro ao alterar Tipo')
            context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Editar Tipo',
            }


            return render(
                request,
                'mecip/create.html',
                context
            )

    form = TypeCourseForm(instance=type_course)
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar Tipo',
    }
    return render(request, 'mecip/create.html', context)
