from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from mecip.models import Curso

def index_course(request):
    course = Curso.objects \
        .order_by('-id')
    paginator = Paginator(course, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'site_title': 'Cursos'
    }

    return render(
        request,
        'mecip/index_course.html',
        context,
    )

def course(request, course_id):

    single_course = get_object_or_404(
        Curso, pk=course_id,
    )
    report = single_course.relatorios.first()


    context = {
        'course': single_course,
        'report': report,
        'site_title': f'Curso - {single_course.type_course}',
    }

    return render(
        request,
        'mecip/course.html',
        context,
    )