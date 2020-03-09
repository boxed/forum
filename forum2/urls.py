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
from django.urls import path, include, re_path
from iommi.admin import Admin

import forum.views as views
import forum2.views
import forum2.views as f2views
import unread.views
import unread.views as unread_views
from crud.views import crud
from issues.models import Issue, Project

urlpatterns = [
    path('', forum2.views.index),
    path('login/', forum2.views.login),
    path('welcome/', forum2.views.welcome),
    path('logout/', forum2.views.logout),
    path('subscriptions/', views.subscriptions),
    path('rooms/', views.rooms),
    path('rooms/<int:room_pk>/', views.view_room),
    path('rooms/<int:room_pk>/write/', views.write),
    path('rooms/<int:room_pk>/message/<int:message_pk>/edit/', views.write),
    path('rooms/<int:room_pk>/message/<int:message_pk>/delete/', views.delete),

    path('subscribe/', unread_views.change_subscription),

    path('wiki/', include('wiki.urls')),
    path('issues/', include('issues.urls')),

    path('', include('authentication.urls')),

    path('api/0/unread_simple/', unread.views.api_unread_simple),
    path('api/0/unread/', unread.views.api_unread),
    path('error_test/', f2views.error_test),
    path('blank/', f2views.blank),

    re_path('issues2/issues/(?P<rest_path>.*)', crud(Issue)),
    re_path('issues2/projects/(?P<rest_path>.*)', crud(Project)),

    path('iommi-admin/', include(Admin.urls())),
]
