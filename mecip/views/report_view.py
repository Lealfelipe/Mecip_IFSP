from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from mecip.models import Relatorio

def index_report(request):
    report = Relatorio.objects \
        .order_by('-id')
    paginator = Paginator(report, 10)
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

    single_report = get_object_or_404(
        Relatorio, pk=report_id,
    )


    context = {
        'report': single_report,
        'site_title': f'Relatorio - {single_report.course}'
    }

    return render(
        request,
        'mecip/report.html',
        context,
    )