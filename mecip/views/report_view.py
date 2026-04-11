from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count
from mecip.models import Report, Campus, Team


def dashboard(request):
    base_reports = Report.objects.all()

    campus_id = request.GET.get('campus')
    team_id = request.GET.get('team')
    status_filter = request.GET.get('status')

    if campus_id:
        base_reports = base_reports.filter(campus_id=campus_id)
    if team_id:
        base_reports = base_reports.filter(assigned_team_id=team_id)

    if request.user.is_authenticated and not request.user.is_superuser:
        user_teams = request.user.teams.all()
        base_reports = base_reports.filter(assigned_team__in=user_teams)
    elif not request.user.is_authenticated:
        base_reports = Report.objects.none()

    reports = base_reports
    if status_filter:
        reports = reports.filter(status=status_filter)

    status_counts = base_reports.values('status').annotate(count=Count('id')).order_by('-count')
    total_reports = base_reports.count()
    campuses = Campus.objects.order_by('campus_name')
    teams = Team.objects.order_by('team_name')

    # Dados para o gráfico de pizza
    status_labels = [item['status'] for item in status_counts]
    status_data = [item['count'] for item in status_counts]

    context = {
        'reports': reports,
        'status_counts': status_counts,
        'total_reports': total_reports,
        'campuses': campuses,
        'teams': teams,
        'selected_campus': campus_id,
        'selected_team': team_id,
        'selected_status': status_filter,
        'status_labels': status_labels,
        'status_data': status_data,
        'site_title': 'Dashboard'
    }

    return render(request, 'mecip/dashboard.html', context)


def index_report(request):
    if request.user.is_authenticated and request.user.is_superuser:
        report_queryset = Report.objects.all()
    elif request.user.is_authenticated:
        user_teams = request.user.teams.all()
        report_queryset = Report.objects.filter(assigned_team__in=user_teams)
    else:
        report_queryset = Report.objects.none()

    report_queryset = report_queryset.order_by('-id')
    paginator = Paginator(report_queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'site_title': 'Relatorios'
    }

    return render(
        request,
        'mecip/index_report.html',
        context,
    )


def report(request, report_id):
    single_report = get_object_or_404(Report, pk=report_id)
    can_assign = False
    if request.user.is_authenticated and single_report.assigned_team and single_report.assigned_user is None:
        can_assign = single_report.assigned_team.users.filter(pk=request.user.pk).exists()

    context = {
        'report': single_report,
        'site_title': f'Relatorio - {single_report.course}',
        'can_assign': can_assign,
    }

    return render(
        request,
        'mecip/report.html',
        context,
    )


def assign_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado para atribuir o relatório.')
        return redirect('mecip:report', report_id=report_id)

    if report.assigned_user is not None:
        messages.error(request, 'Relatório já está atribuído a um usuário.')
        return redirect('mecip:report', report_id=report_id)

    if report.assigned_team is None:
        messages.error(request, 'Relatório não tem equipe atribuída.')
        return redirect('mecip:report', report_id=report_id)

    if not report.assigned_team.users.filter(pk=request.user.pk).exists():
        messages.error(request, 'Você não pertence à equipe atribuída deste relatório.')
        return redirect('mecip:report', report_id=report_id)

    report.assigned_user = request.user
    report.status = 'Em andamento'
    report.save()
    messages.success(request, 'Relatório atribuído a você com sucesso.')
    return redirect('mecip:report', report_id=report_id)
