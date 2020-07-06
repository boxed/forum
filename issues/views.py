from iommi import (
    Field,
    Form,
    html,
    Page,
    Table,
)
from iommi.form import (
    create_object__post_handler,
)

from forum.models import Room
from forum.views import (
    RoomPage,
)
from forum2 import decode_url
from issues.models import (
    Issue,
    Project,
)
from unread import unread_handling


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


@decode_url(Project, Issue)
@unread_handling(Issue)
def view_issue(request, project, issue, unread_data):
    # TODO: when you write a comment you get redirected to the room, not the issue
    assert issue.project == project

    class IssuePage(Page):
        title = html.h1(issue.name)

        user_properties = html.ul(
            attrs__class__properties=True,
            children={
                x.name: html.li(
                    f'{x.name}: {x.data}',
                    attrs__class=dict(
                        unread=unread_data.is_unread(x.last_changed_time),
                        unread2=unread_data.is_unread2(x.last_changed_time),
                    ),
                )
                for x in issue.user_properties.all()
            }
        )

        text_properties = html.ul(
            attrs__class__properties=True,
            children={
                x.name: html.li(
                    f'{x.name}: {x.data}',
                    attrs__class=dict(
                        unread=unread_data.is_unread(x.last_changed_time),
                        unread2=unread_data.is_unread2(x.last_changed_time),
                    ),
                )
                for x in issue.text_properties.all()
            }
        )

        comments = RoomPage(room=issue.comments, unread_data=unread_data, parts__header__template='forum/blank.html') if issue.comments_id else None

    return IssuePage()


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
