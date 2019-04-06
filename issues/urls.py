from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_project_list),
    path('<str:project_name>/', views.view_project),
    path('<str:project_name>/<str:issue_name>/', views.view_issue),
]
