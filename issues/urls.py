from django.urls import path
from iommi import Form

from . import views
from .models import (
    Project,
)

urlpatterns = [
    path('', views.view_project_list),
    path('create/', Form.create(auto__model=Project).as_view()),
    path('projects/<str:project_name>/', views.view_project),
    path('projects/<str:project_name>/create/', views.create_issue),
    path('projects/<str:project_name>/issues/<int:issue_pk>/', views.view_issue),
]
