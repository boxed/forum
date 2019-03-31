from django.shortcuts import render
from tri.table import render_table_to_response

from wiki.models import Context, Document, DocumentVersion


def view_context_list(request):
    return render_table_to_response(
        request=request,
        table__data=Context.objects.all().order_by('name'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
        table__column__name__cell__format=lambda value, row, **_: value if value != 'Private wiki' else f'Private wiki for {row.custom_data}',
        table__include=['name'],
        context=dict(title='Wiki contexts'),
        template='wiki/list.html',
    )


def view_context(request, context_name):
    return render_table_to_response(
        request=request,
        table__data=Document.objects.filter(context__name__iexact=context_name).order_by('pk'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
        table__include=['name'],
        context=dict(title=f'Documents of context {Context.objects.get(name__iexact=context_name)}'),
        template='wiki/list.html',
    )


def view_document(request, context_name, document_name):
    doc = Document.objects.get(context__name__iexact=context_name, name__iexact=document_name)
    return render(request, 'wiki/document.html', context=dict(document_version=doc.versions.all().order_by('pk')[0]))


def view_version_list(request, context_name, document_name):
    return render_table_to_response(
        request=request,
        table__data=DocumentVersion.objects.filter(context__name__iexact=context_name, document__name__iexact=document_name),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
        template='wiki/list.html',
    )


def view_version(request, context_name, document_name, version_pk):
    return render(request, 'wiki/document.html', context=dict(document_version=DocumentVersion.objects.get(pk=version_pk)))
