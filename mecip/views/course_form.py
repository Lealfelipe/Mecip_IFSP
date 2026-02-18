from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import CampusForm, CourseForm
from django.urls import reverse
from mecip.models import Campus, Curso
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def create_course(request):
    form_action = reverse('mecip:create_course')

    if request.method == 'POST':
        form = CourseForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Curso'
        }

        if form.is_valid():
            course = form.save()
            messages.success(request, 'Curso cadastrado com sucesso')
            return redirect('mecip:update_course', course_id= course.pk)
        
        else:
            messages.error(request, 'Erro ao cadastrar curso')


        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': CourseForm(),
        'form_action': form_action,
        'site_title': 'Criar Curso'
    }
    return render(
        request,
        'mecip/create.html',
        context
    )

@user_passes_test(is_admin)
def update_course(request, course_id):
    course = get_object_or_404(Curso, pk= course_id)
    form_action = reverse('mecip:update_course', args=(course_id,))

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)

        

        if form.is_valid():
            form.save()
            messages.success(request, 'Curso alterado com sucesso')
            return redirect('mecip:update_course', course_id=course.id)

        else:
            messages.error(request, 'Erro ao alterar Curso')
            context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Editar Curso',
            }


            return render(
                request,
                'mecip/create.html',
                context
            )

    form = CourseForm(instance=course)
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar Curso',
    }
    return render(request, 'mecip/create.html', context)
