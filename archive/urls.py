from django.urls import path

from . import views

urlpatterns = [
    path('<path:path>', views.index),
    path('', views.index),
]
