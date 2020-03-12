from difflib import SequenceMatcher

from django.shortcuts import (
    render,
)
from django.utils.safestring import mark_safe
from iommi import Table

from forum2 import decode_url
from unread import (
    unread_handling,
    is_unread,
)
from wiki.models import Context, Document, DocumentVersion


def view_context_list(request):
    return Table(
        auto__model=Context,
        auto__include=['name'],
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
        columns__name__cell__format=lambda value, row, **_: value if value != 'Private wiki' else f'Private wiki for {row.custom_data}',
        title='Wiki contexts',
    )


@decode_url(Context)
def view_context(request, context):
    return Table(
        title=f'Documents of context {context}',
        auto__rows=Document.objects.filter(context=context),
        auto__include=['name'],
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
        row__attrs__class__unread=lambda row, **_: is_unread(user=request.user, identifier=row.get_unread_identifier()),
    )


@decode_url(Context, Document)
@unread_handling(Document)
def view_document(request, context, document, unread_data):
    assert context == document.context
    document_version = document.versions.all().order_by('-pk')[0]
    return render(request, 'wiki/document.html', context=dict(title=document_version.name, document_version=document_version))


@decode_url(Context, Document)
def view_version_list(request, context, document):
    return Table(
        title=f'Versions of {document}',
        auto__include=['name', 'version', 'changed_time'],
        auto__rows=DocumentVersion.objects.filter(document=document).order_by('version'),
        columns__version__cell__url=lambda row, **_: row.get_absolute_url(),
    )


@decode_url(Context, Document, DocumentVersion)
def view_version(request, context, document, document_version):
    return render(request, 'wiki/document.html', context=dict(document_version=document_version))


@decode_url(Context, Document, DocumentVersion)
def view_diff(request, context, document, document_version, version_pk_2):
    doc_b = DocumentVersion.objects.get(pk=version_pk_2)
    a = document_version.content
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

    return render(request, 'wiki/diff.html', context=dict(a=document_version, b=doc_b, diff=mark_safe(diff)))


def edit(request, context_name, document_name):
    doc = Document.objects.get(context__name__iexact=context_name, name__iexact=document_name)
    document_version = doc.versions.all().order_by('-pk')[0]
    # TODO:
    #   - on save, validate that no one has edited in the meantime
    return create_object(
        request=request,
        model=DocumentVersion,
        form__exclude=['changed_time'],
        form__field=dict(
            document=dict(
                initial=doc,
                editable=False,
                call_target=Field.hidden,
            ),
            name__initial=document_version.name,
            content=dict(
                initial=document_version.content,
                call_target=Field.textarea,
                attrs__style=dict(
                    height='40rem',
                    width='50rem',
                ),
            ),
            custom_data__initial=document_version.custom_data,
            version=dict(
                initial=document_version.version + 1,
                editable=False,
                call_target=Field.hidden,
            ),
        ),
    )
