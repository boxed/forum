from django.shortcuts import render

from forum.views import render_room
from issues.models import (
    Issue,
    Project,
)
from tri_portal import (
    Page,
)


# TODO: both these views output should have a <div class="content_text"> around them to match the styling in the CSS
def view_project_list(request):
    return Page.table_page(
        title='Projects',
        contents__table=dict(
            data=Project.objects.all().order_by('name'),
            column__name__cell__url=lambda row, **_: row.get_absolute_url(),
            include=['name'],
        ),
    ).respond_or_render(request)


def view_project(request, project_name):
    project = Project.objects.get(name=project_name)

    return Page.table_page(
        title=f'Issues for {project}',
        contents__table=dict(
            data=Issue.objects.filter(project=project).order_by('pk'),
            column__name__cell__url=lambda row, **_: row.get_absolute_url(),
            include=['name'],
        ),
    ).respond_or_render(request)


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

