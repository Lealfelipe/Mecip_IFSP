from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from mecip.forms import ReportForm
from django.urls import reverse
from mecip.models import Relatorio, Curso, Campus
from django.contrib import messages

# from django.contrib.auth.decorators import user_passes_test

def create_report(request):
    form_action = reverse('mecip:create_report')

    if request.method == 'POST':
        form = ReportForm(request.POST)

        context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Criar Relatorio',
        }

        if form.is_valid():
            course = form.cleaned_data['course']
            campus = form.cleaned_data['campus']

            curso_exists = Curso.objects.filter(type_course=course.type_course, campus=campus).exists()

            if not curso_exists:
                messages.error(request, 'Curso não disponível nesse Campus')
            else:
                if Relatorio.objects.filter(course=course, campus=campus).exists():
                    messages.error(request, 'Já existe um relatório para este curso neste campus.')
                else:
                    report = form.save()
                    messages.success(request, 'Relatório criado com sucesso!')
                    return redirect('mecip:update_report', report_id=report.pk)
            
        return render(
            request,
            'mecip/create.html',
            context
        )

    context = {
        'form': ReportForm(),
        'form_action': form_action,
        'site_title': 'Criar Relatorio',
    }
    return render(
        request,
        'mecip/create.html',
        context
    )

def create_report_params(request, course_id, campus_id):
    course = get_object_or_404(Curso, pk=course_id)
    campus = get_object_or_404(Campus, pk=campus_id)
    form_action = reverse('mecip:create_report_params', args=[course_id, campus_id])

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save(commit=False)
            if report.course != course or report.campus != campus:
                messages.error(request, "Não é possível criar o relatório")
            
            else:
                report.course = course  
                report.campus = campus
                report.save()
                messages.success(request, "Relatório criado com sucesso!")
                return redirect('mecip:update_report', report_id=report.pk)
    else:
        initial_data = {'course': course, 'campus': course.campus}
        form = ReportForm(initial=initial_data)

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Criar Relatório',
    }
    return render(request, 'mecip/create.html', context)


def update_report(request, report_id):
    report = get_object_or_404(Relatorio, pk= report_id)
    form_action = reverse('mecip:update_report', args=(report_id,))

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)

        

        if form.is_valid():
            form.save()
            messages.success(request, 'Relatório alterado com sucesso!')

            return redirect('mecip:update_report', report_id=report.id)

        else:
            messages.error(request, 'Erro ao alterar o relatório. Já existe um relatório para o curso e campus.')

            context = {
            'form': form,
            'form_action': form_action,
            'site_title': 'Editar Relatorio',
            }


            return render(
                request,
                'mecip/create.html',
                context
            )

    form = ReportForm(instance=report)
    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar Relatorio',
    }
    return render(request, 'mecip/create.html', context)