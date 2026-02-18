from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import CampusForm
from django.urls import reverse
from mecip.models import Campus
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def create(request):
    form_action = reverse('mecip:create')

    if request.method == 'POST':
        form = CampusForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Campus',
        }

        if form.is_valid():
            campus = form.save()
            messages.success(request, 'Campus inserido com sucesso!')
            return redirect('mecip:update', campus_id= campus.pk)
        
        else:
            messages.success(request, 'Erro ao inserir Campus')


        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': CampusForm(),
        'form_action': form_action,
        'site_title': 'Criar Campus',
    }
    return render(
        request,
        'mecip/create.html',
        context
    )


@user_passes_test(is_admin)
def update(request, campus_id):
    campus = get_object_or_404(Campus, pk= campus_id)
    form_action = reverse('mecip:update', args=(campus_id,))

    if request.method == 'POST':
        form = CampusForm(request.POST, instance=campus)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Editar Campus',
        }

        if form.is_valid():
            campus = form.save()
            messages.success(request, 'Campus alterado com sucesso!')
            return redirect('mecip:update', campus_id)
        
        else:
            messages.error(request, 'Erro ao alterar Campus')



        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': CampusForm(instance=campus),
        'form_action': form_action,
        'site_title': 'Editar Campus',
    }
    return render(
        request,
        'mecip/create.html',
        context
    )


