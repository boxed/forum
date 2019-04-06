from django.shortcuts import render
from tri.table import render_table_to_response

from forum.views import render_room
from issues.models import Project, Issue


def view_project_list(request):
    return render_table_to_response(
        request=request,
        table__data=Project.objects.all().order_by('name'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
        table__include=['name'],
        context=dict(title='Projects'),
        template='wiki/list.html',  # TODO: Fix when tri.table has base_template
    )


def view_project(request, project_name):
    project = Project.objects.get(name=project_name)
    return render_table_to_response(
        request=request,
        table__data=Issue.objects.filter(project=project).order_by('pk'),
        table__column__name__cell__url=lambda row, **_: row.get_absolute_url(),
        table__include=['name'],
        context=dict(title=f'Issues for {project}'),
        template='wiki/list.html',  # TODO: Fix when tri.table has base_template
    )


def view_issue(request, project_name, issue_name):
    project = Project.objects.get(name=project_name)
    issue = Issue.objects.get(project=project, name=issue_name)
    return render(
        request=request,
        template_name='issues/view_issue.html',
        context=dict(
            issue=issue,
            project=project,
            comments=render_room(
                request,
                room_pk=issue.comments_id,
                base_template='forum/base_content.html',
                room_header_template='forum/blank.html',
            ),
        ),
    )
