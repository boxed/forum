"""forum2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
import forum.views as views
import forum2.views as f2views

urlpatterns = [
    path('', views.index),
    path('login/', views.login),
    path('welcome/', views.welcome),
    path('logout/', views.logout),
    path('subscriptions/', views.subscriptions),
    path('rooms/', views.rooms),
    path('rooms/<int:room_pk>/', views.view_room),
    path('rooms/<int:room_pk>/write/', views.write),
    path('rooms/<int:room_pk>/message/<int:message_pk>/edit/', views.write),
    path('rooms/<int:room_pk>/message/<int:message_pk>/delete/', views.delete),

    path('api/0/unread_simple/', views.api_unread_simple),
    path('api/0/unread/', views.api_unread),
    path('error_test/', f2views.error_test),
]
