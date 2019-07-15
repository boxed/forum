from django.http import HttpResponse
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
from tri_portal_3 import bind


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


# class PropertiesContent(PageContent):
#     pass
#
#
# class RoomContent(PageContent):
#     pass
#
#
def view_issue(request, project_name, issue_name):
    project = Project.objects.get(name=project_name)
    issue = Issue.objects.get(project=project, name=issue_name)

    def properties(x):
        return {
            p.name: dict(
                tag='div',
                attrs__class__property=True,
                children=dict(
                    label=dict(tag='label', content=p.name),
                    content=dict(tag='span', content=p.data),
                )
            )
            for p in x.all()
        }

    return HttpResponse(bind(
        children=dict(
            title=dict(tag='h1', content=issue),

            user_properties__children=properties(issue.user_properties),
            text_properties__children=properties(issue.text_properties),
            long_text_properties__children=properties(issue.long_text_properties),

            separator=dict(tag='hr'),

            # comments=room(issue.comments),
        ),

    ).render2(request))  # TODO: this should be render_or_respond() but we haven't implemented this in the new fancy code
