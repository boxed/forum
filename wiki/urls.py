from django.urls import path
from . import views

urlpatterns = [
    path('', views.contexts),
    path('<int:context_pk>/', views.documents),
    path('<int:context_pk>/<int:document_pk>/', views.document),
    path('<int:context_pk>/<str:document_name>/', views.document_by_name),
    path('<int:context_pk>/<int:document_pk>/versions/', views.versions),
    path('<int:context_pk>/<int:document_pk>/<int:version_pk>/', views.version),
]
