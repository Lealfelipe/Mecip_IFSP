from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from mecip.models import Campus


def index(request):
    campus = Campus.objects \
        .order_by('-id')
    paginator = Paginator(campus, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'site_title': 'Campus'
    }

    return render(
        request,
        'mecip/index.html',
        context,
    )

def campus(request, campus_id):

    single_campus = get_object_or_404(
        Campus, pk=campus_id,
    )

    site_title = f'IFSP - {single_campus.city}'

    context = {
        'campus': single_campus,
        'site_title': site_title
    }

    return render(
        request,
        'mecip/campus.html',
        context,
    )