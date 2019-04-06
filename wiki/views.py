from difflib import SequenceMatcher

from django.shortcuts import render
from django.utils.safestring import mark_safe
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
        template='wiki/list.html',   # TODO: Fix when tri.table has base_template
    )


def view_context(request, context_name):
    return render_table_to_response(
        request=request,
        table__data=Document.objects.filter(context__name__iexact=context_name).order_by('pk'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
        table__include=['name'],
        context=dict(title=f'Documents of context {Context.objects.get(name__iexact=context_name)}'),
        template='wiki/list.html',  # TODO: Fix when tri.table has base_template
    )


def view_document(request, context_name, document_name):
    doc = Document.objects.get(context__name__iexact=context_name, name__iexact=document_name)
    return render(request, 'wiki/document.html', context=dict(document_version=doc.versions.all().order_by('pk')[0]))


def view_version_list(request, context_name, document_name):
    doc = Document.objects.get(context__name__iexact=context_name, name__iexact=document_name)
    return render_table_to_response(
        request=request,
        context=dict(
            title=f'Versions of {doc}',
        ),
        table__data=DocumentVersion.objects.filter(document=doc).order_by('version'),
        table__include=['name', 'version', 'changed_time'],
        table__column__version__cell__url=lambda row, **_: row.get_absolute_url(),
        template='wiki/list.html',  # TODO: Fix when tri.table has base_template
    )


def view_version(request, context_name, document_name, version_pk):
    return render(request, 'wiki/document.html', context=dict(document_version=DocumentVersion.objects.get(pk=version_pk)))


def view_diff(request, context_name, document_name, version_pk, version_pk_2):
    doc_a = DocumentVersion.objects.get(pk=version_pk)
    doc_b = DocumentVersion.objects.get(pk=version_pk_2)
    a = doc_a.content
    b = doc_b.content

    diff = ''
    s = SequenceMatcher(lambda x: x in " \t", a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        a_side = a[i1:i2]
        b_side = b[j1:j2]
        if tag == 'equal':
            diff += a_side
        elif tag == 'delete':
            diff += f'<del>{a_side}</del>'
        elif tag == 'replace':
            diff += f'<del>{a_side}</del>'
            diff += f'<ins>{b_side}</ins>'
        elif tag == 'insert':
            diff += f'<ins>{b_side}</ins>'
        else:
            assert False, f'unknown op code {tag}'

    return render(request, 'wiki/diff.html', context=dict(a=doc_a, b=doc_b, diff=mark_safe(diff)))
