from django.shortcuts import render
from iommi import (
    Table,
    Form,
    Field,
)
from iommi.form import (
    create_object__post_handler,
)

from forum.models import Room
from forum.views import render_room
from issues.models import Project, Issue


def view_project_list(request):
    return Table(
        auto__model=Project,
        auto__include=['name'],
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
        actions__create_project__attrs__href='create/'
    )


def view_project(request, project_name):
    project = Project.objects.get(name=project_name)
    return Table(
        title=f'Issues for {project}',
        auto__model=Issue,
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
        actions__create_issue__attrs__href='create/'
    )


def view_issue(request, project_name, pk):
    project = Project.objects.get(name=project_name)
    issue = Issue.objects.get(project=project, pk=pk)
    return render(
        request=request,
        template_name='issues/view_issue.html',
        context=dict(
            issue=issue,
            project=project,
            comments=render_room(
                request,
                room_pk=issue.comments_id,
                room_header_template='forum/blank.html',
            ) if issue.comments_id else None,
        ),
    )


def create_issue(request, project_name):
    project = Project.objects.get(name=project_name)

    def post_handler(form, **kwargs):
        result = create_object__post_handler(form=form, **kwargs)
        if form.is_valid():
            form.instance.comments = Room.objects.create(name=f'Issue comments {project}/{form.instance}', custom_data=f'issues/{project.pk}/{form.instance.pk}')
            form.instance.save()
        return result

    return Form.create(
        auto__model=Issue,
        auto__exclude=['time_created', 'last_changed_time', 'comments'],
        fields__project=Field.hidden(editable=False, initial=project),
        fields__last_changed_by=Field.hidden(editable=False, initial=request.user),
        actions__submit__post_handler=post_handler,
    )
