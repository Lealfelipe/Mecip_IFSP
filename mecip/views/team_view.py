from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from mecip.models import Team


def index_team(request):
    if request.user.is_superuser:
        teams = Team.objects.order_by('-id')
    else:
        teams = Team.objects.filter(users=request.user).order_by('-id')

    paginator = Paginator(teams, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'site_title': 'Equipes'
    }

    return render(
        request,
        'mecip/index_team.html',
        context,
    )


def team(request, team_id):
    # Para usuários não superuser, garante que só vejam equipes onde estão inscritos
    if request.user.is_superuser:
        single_team = get_object_or_404(Team, pk=team_id)
    else:
        single_team = get_object_or_404(Team, pk=team_id, users=request.user)

    site_title = f'Equipe - {single_team.team_name}'

    context = {
        'team': single_team,
        'site_title': site_title
    }

    return render(
        request,
        'mecip/team.html',
        context,
    )