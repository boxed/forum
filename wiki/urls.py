from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_context_list),
    path('<str:context_name>/', views.view_context),
    path('<str:context_name>/<str:document_name>/', views.view_document),
    path('<str:context_name>/<str:document_name>/versions/', views.view_version_list),
    path('<str:context_name>/<str:document_name>/<int:version_pk>/', views.view_version),
    path('<str:context_name>/<str:document_name>/<int:version_pk>/<int:version_pk_2>/', views.view_diff),
    path('<str:context_name>/<str:document_name>/edit/', views.edit),
]
