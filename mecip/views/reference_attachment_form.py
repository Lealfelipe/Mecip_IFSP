from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from mecip.forms import ReferenceAttachmentForm
from mecip.models import ReferenceAttachment
from mecip.permissions import access_required, can_manage_records


@access_required(can_manage_records)
def index_reference_attachment(request):
    reference_attachments = ReferenceAttachment.objects.order_by('name')
    paginator = Paginator(reference_attachments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'site_title': 'Anexos de referencia',
    }
    return render(request, 'mecip/index_reference_attachment.html', context)


@access_required(can_manage_records)
def create_reference_attachment(request):
    form_action = reverse('mecip:create_reference_attachment')

    if request.method == 'POST':
        form = ReferenceAttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            reference_attachment = form.save()
            messages.success(request, 'Anexo de referencia cadastrado com sucesso.')
            return redirect('mecip:update_reference_attachment', reference_attachment_id=reference_attachment.pk)

        messages.error(request, 'Erro ao cadastrar anexo de referencia.')
    else:
        form = ReferenceAttachmentForm()

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Criar anexo de referencia',
    }
    return render(request, 'mecip/reference_attachment_form.html', context)


@access_required(can_manage_records)
def update_reference_attachment(request, reference_attachment_id):
    reference_attachment = get_object_or_404(ReferenceAttachment, pk=reference_attachment_id)
    form_action = reverse('mecip:update_reference_attachment', args=(reference_attachment_id,))

    if request.method == 'POST':
        form = ReferenceAttachmentForm(request.POST, request.FILES, instance=reference_attachment)

        if form.is_valid():
            form.save()
            messages.success(request, 'Anexo de referencia alterado com sucesso.')
            return redirect('mecip:update_reference_attachment', reference_attachment_id=reference_attachment.id)

        messages.error(request, 'Erro ao alterar anexo de referencia.')
    else:
        form = ReferenceAttachmentForm(instance=reference_attachment)

    context = {
        'form': form,
        'form_action': form_action,
        'site_title': 'Editar anexo de referencia',
        'reference_attachment': reference_attachment,
    }
    return render(request, 'mecip/reference_attachment_form.html', context)


@access_required(can_manage_records)
def delete_reference_attachment(request, reference_attachment_id):
    reference_attachment = get_object_or_404(ReferenceAttachment, pk=reference_attachment_id)

    if request.method == 'POST':
        if reference_attachment.answer_attachments.exists():
            messages.error(
                request,
                'Este anexo nao pode ser excluido porque esta relacionado '
                'a uma ou mais respostas.'
            )
            return redirect('mecip:index_reference_attachment')

        reference_attachment.delete()
        messages.success(request, 'Anexo de referencia excluido com sucesso.')
        return redirect('mecip:index_reference_attachment')

    return redirect('mecip:index_reference_attachment')
