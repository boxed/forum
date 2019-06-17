from django.shortcuts import get_object_or_404
from django.urls import path, URLResolver
from django.urls.resolvers import RegexPattern
from tri_declarative import dispatch, EMPTY, evaluate
from tri_form.views import create_object, edit_object
from tri_table import render_table_to_response, Column, Link


@dispatch(
    title=lambda model, **_: model._meta.verbose_name,
)
def list(request, model, title):
    return render_table_to_response(
        request=request,
        table__model=model,
        table__column__name__cell__url=lambda row, **_: f'{row.pk}/',
        table__extra_fields=[
            Column.edit(after=0, cell__url=lambda row, **_: f'{row.pk}/edit/'),
            Column.delete(after=0, cell__url=lambda row, **_: f'{row.pk}/delete/'),
        ],
        template='wiki/list.html',
        context=dict(
            title=evaluate(title, model=model),
        ),
        links=[
            Link(f'Create {model._meta.verbose_name}', attrs__href='create/')
        ]
    )


@dispatch(
    title=lambda model, **_: model._meta.verbose_name,
)
def view(request, model, pk, title):
    return edit_object(
        request=request,
        instance=get_object_or_404(model, pk=pk),
        form__editable=False,
        form__links=[],
        render__context__title=evaluate(title, model=model),
    )


@dispatch(
    title=lambda model, **_: model._meta.verbose_name,
)
def create(request, model, title):
    return create_object(
        request=request,
        model=model,
        render__context__title=evaluate(title, model=model),
    )


@dispatch(
    title=lambda model, **_: model._meta.verbose_name,
)
def update(request, model, pk, title):
    return edit_object(
        request=request,
        instance=get_object_or_404(model, pk=pk),
        render__context__title=evaluate(title, model=model),
    )


@dispatch(
    title=lambda model, **_: model._meta.verbose_name,
)
def delete(request, model, pk, title):
    return delete_object(
        request=request,
        model=model,
        instance=get_object_or_404(model, pk=pk),
        render__context__title=evaluate(title, model=model),
    )


urlpatterns = [
    path('', list),
    path('<int:pk>/', view),
    path('create/', create),
    path('<int:pk>/edit/', update),
    path('<int:pk>/delete/', delete),
]


@dispatch(
    list=EMPTY,
    view=EMPTY,
    create=EMPTY,
    update=EMPTY,
    delete=EMPTY,
    all=EMPTY,
)
def crud(model, all, **kwargs):
    def crud_impl(request, rest_path):
        m = URLResolver(RegexPattern(r'^'), urlpatterns).resolve(rest_path)
        return m.func(request=request, model=model, **all, **kwargs[m.func.__name__], **m.kwargs)

    return crud_impl
