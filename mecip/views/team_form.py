from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import TeamForm
from django.urls import reverse
from mecip.models import Team
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def create_team(request):
    form_action = reverse('mecip:create_team')

    if request.method == 'POST':
        form = TeamForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Equipe',
        }

        if form.is_valid():
            team = form.save()
            messages.success(request, 'Equipe inserida com sucesso!')
            return redirect('mecip:update_team', team_id= team.pk)
        
        else:
            messages.success(request, 'Erro ao inserir Time')


        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': TeamForm(),
        'form_action': form_action,
        'site_title': 'Criar Equipe',
    }
    return render(
        request,
        'mecip/create.html',
        context
    )

@user_passes_test(is_admin)
def update_team(request, team_id):
    team = get_object_or_404(Team, pk= team_id)
    form_action = reverse('mecip:update_team', args=(team_id,))

    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Editar Equipe',
        }

        if form.is_valid():
            team = form.save()
            messages.success(request, 'Equipe editada com sucesso!')
            return redirect('mecip:update_team', team_id= team.pk)
        
        else:
            messages.success(request, 'Erro ao editar Equipe')


        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': TeamForm(instance=team),
        'form_action': form_action,
        'site_title': 'Editar Equipe',
    }
    return render(
        request,
        'mecip/create.html',
        context
    )


@user_passes_test(is_admin)
def add_user_to_team(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        
        if team.users.filter(pk=user.pk).exists():
            messages.warning(request, f'O usuário {user.get_full_name() or user.username} já pertence a esta equipe.')
        else:
            team.users.add(user)
            messages.success(request, f'Usuário {user.get_full_name() or user.username} adicionado à equipe!')
        
        return redirect('mecip:add_user_to_team', team_id=team.pk)
    
    available_users = User.objects.exclude(pk__in=team.users.all())
    context = {
        'team': team,
        'available_users': available_users,
        'site_title': f'Adicionar Usuário - {team.team_name}',
    }
    return render(request, 'mecip/add_user_to_team.html', context)

 
@user_passes_test(is_admin)
def remove_user_from_team(request, team_id, user_id):
    team = get_object_or_404(Team, pk=team_id)
    user = get_object_or_404(User, pk=user_id)

    context = {
        'team': team,
        'user_to_remove': user,
        'site_title': f'Remover Usuário - {team.team_name}',
    }

    if request.method == 'POST':
        if team.users.filter(pk=user.pk).exists():
            team.users.remove(user)
            messages.success(request, f'Usuário {user.get_full_name() or user.username} removido da equipe!')
        else:
            messages.warning(request, f'O usuário {user.get_full_name() or user.username} não pertence a esta equipe.')

        return redirect('mecip:remove_user_from_team', team_id=team.pk, user_id=user.pk)
       

    # GET: exibe página de confirmação de remoção
    return render(request, 'mecip/remove_user_to_team.html', context)