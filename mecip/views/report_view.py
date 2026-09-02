from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from io import BytesIO
from mecip.models import Report, Campus, Course, Team
from mecip.permissions import (
    access_denied_response,
    can_view_all_records,
    can_view_report_questionnaire,
)


def dashboard(request):
    accessible_reports = Report.objects.all()

    campus_id = request.GET.get('campus')
    course_id = request.GET.get('course')
    year_filter = request.GET.get('year')
    team_id = request.GET.get('team')
    status_filter = request.GET.get('status')
    sort_field = request.GET.get('sort', 'created')
    sort_direction = request.GET.get('direction', 'desc')

    if request.user.is_authenticated and not can_view_all_records(request.user):
        user_teams = request.user.teams.all()
        accessible_reports = accessible_reports.filter(
            assigned_team__in=user_teams
        )
    elif not request.user.is_authenticated:
        accessible_reports = Report.objects.none()

    courses = (
        Course.objects
        .filter(relatorios__in=accessible_reports)
        .select_related('type_course', 'campus')
        .distinct()
        .order_by('type_course__type_name_course', 'campus__campus_name')
    )
    years = (
        accessible_reports.order_by()
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )

    base_reports = accessible_reports
    if campus_id:
        base_reports = base_reports.filter(campus_id=campus_id)
    if course_id:
        base_reports = base_reports.filter(course_id=course_id)
    if year_filter:
        base_reports = base_reports.filter(year=year_filter)
    if team_id:
        base_reports = base_reports.filter(assigned_team_id=team_id)

    reports = base_reports
    if status_filter:
        reports = reports.filter(status=status_filter)

    sort_fields = {
        'course': 'course__type_course__type_name_course',
        'year': 'year',
        'created': 'created_date',
    }
    if sort_field not in sort_fields:
        sort_field = 'created'
    if sort_direction not in ('asc', 'desc'):
        sort_direction = 'desc'

    order_prefix = '' if sort_direction == 'asc' else '-'
    reports = reports.select_related(
        'course__type_course',
        'campus',
        'assigned_team',
    ).order_by(
        f'{order_prefix}{sort_fields[sort_field]}',
        'id',
    )

    status_counts = list(
        base_reports.values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    total_reports = base_reports.count()
    campuses = Campus.objects.order_by('campus_name')
    teams = Team.objects.order_by('team_name')

    def dashboard_query(**changes):
        parameters = request.GET.copy()
        for key, value in changes.items():
            if value is None:
                parameters.pop(key, None)
            else:
                parameters[key] = value
        return parameters.urlencode()

    for item in status_counts:
        item['query_string'] = dashboard_query(status=item['status'])

    def sort_query(field):
        next_direction = (
            'desc'
            if sort_field == field and sort_direction == 'asc'
            else 'asc'
        )
        return dashboard_query(sort=field, direction=next_direction)

    # Dados para o gráfico de pizza
    status_labels = [item['status'] for item in status_counts]
    status_data = [item['count'] for item in status_counts]

    context = {
        'reports': reports,
        'status_counts': status_counts,
        'total_reports': total_reports,
        'campuses': campuses,
        'courses': courses,
        'years': years,
        'teams': teams,
        'selected_campus': campus_id,
        'selected_course': course_id,
        'selected_year': year_filter,
        'selected_team': team_id,
        'selected_status': status_filter,
        'selected_sort': sort_field,
        'selected_direction': sort_direction,
        'all_reports_query': dashboard_query(status=None),
        'course_sort_query': sort_query('course'),
        'year_sort_query': sort_query('year'),
        'created_sort_query': sort_query('created'),
        'status_labels': status_labels,
        'status_data': status_data,
        'site_title': 'Dashboard'
    }

    return render(request, 'mecip/dashboard.html', context)


def index_report(request):
    if request.user.is_authenticated and can_view_all_records(request.user):
        report_queryset = Report.objects.all()
    elif request.user.is_authenticated:
        user_teams = request.user.teams.all()
        report_queryset = Report.objects.filter(assigned_team__in=user_teams)
    else:
        report_queryset = Report.objects.none()

    report_queryset = report_queryset.order_by('-year', '-id')
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
    if not can_view_report_questionnaire(request.user, single_report):
        return access_denied_response(request)

    can_assign = False
    if request.user.is_authenticated and single_report.assigned_team and single_report.assigned_user is None:
        can_assign = single_report.assigned_team.users.filter(pk=request.user.pk).exists()

    context = {
        'report': single_report,
        'site_title': f'Relatorio - {single_report.course} - {single_report.year}',
        'can_assign': can_assign,
    }

    return render(
        request,
        'mecip/report.html',
        context,
    )


def report_pdf_download(request, report_id):
    single_report = get_object_or_404(Report, pk=report_id)
    if not can_view_report_questionnaire(request.user, single_report):
        return access_denied_response(request)

    pdf_bytes = _build_report_pdf(single_report, request)

    if pdf_bytes is None:
        messages.error(request, 'Nao foi possivel gerar o PDF do relatorio.')
        return redirect('mecip:report', report_id=report_id)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="relatorio_{single_report.course}_'
        f'{single_report.campus.campus_name}_{single_report.year}.pdf"'
    )
    return response


def _build_report_pdf(report: Report, request):
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None

    answers = (
        report.answers
        .filter(question__section__questionnaire=report.questionnaire)
        .select_related('question__section', 'selected_answer_option')
        .prefetch_related('attachments__reference_attachment')
        .order_by(
            'question__section__order',
            'question__section__name',
            'question__order',
        )
    )

    for answer in answers:
        for attachment in answer.attachments.all():
            public_path = attachment.public_path
            attachment.pdf_url = (
                f'{settings.PUBLIC_BASE_URL}{public_path}'
                if settings.PUBLIC_BASE_URL
                else request.build_absolute_uri(public_path)
            )

    html = render_to_string(
        'mecip/report_pdf.html',
        {
            'report': report,
            'answers': answers,
        },
    )
    output = BytesIO()
    pdf = pisa.CreatePDF(src=html, dest=output, encoding='utf-8')
    if pdf.err:
        return None
    return output.getvalue()


@require_POST
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
