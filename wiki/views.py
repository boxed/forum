from django.shortcuts import render
from tri.table import render_table_to_response

from wiki.models import Context, Document, DocumentVersion


def contexts(request):
    return render_table_to_response(
        request=request,
        table__data=Context.objects.all().order_by('name'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
    )


def documents(request, context_pk):
    return render_table_to_response(
        request=request,
        table__data=Document.objects.filter(context__pk=context_pk).order_by('pk'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
    )


def document(request, context_pk, document_pk):
    del context_pk
    doc = Document.objects.get(pk=document_pk)
    return render(request, 'wiki/document.html', context=dict(document_version=doc.versions.all().order_by('pk')[0]))


def versions(request, context_pk, document_pk):
    del context_pk
    return render_table_to_response(
        request=request,
        table__data=DocumentVersion.objects.filter(document__pk=document_pk),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
    )


def version(request, context_pk, document_pk, version_pk):
    del context_pk, document_pk
    return render(request, 'wiki/document.html', context=dict(document_version=DocumentVersion.objects.get(pk=version_pk)))
