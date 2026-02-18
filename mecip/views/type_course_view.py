from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from mecip.models import Type_Course

def index_type_course(request):
    type_course = Type_Course.objects \
        .order_by('-id')
    paginator = Paginator(type_course, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'site_title': 'Tipos'
    }

    return render(
        request,
        'mecip/index_type_course.html',
        context,
    )

def type_course(request, type_course_id):

    single_type = get_object_or_404(
        Type_Course, pk=type_course_id,
    )


    context = {
        'type_course': single_type,
        'site_title': f'Curso - {single_type.type_name_course}',
    }

    return render(
        request,
        'mecip/type.html',
        context,
    )