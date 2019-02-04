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
import forum2.forum.views as views

urlpatterns = [
    path('convert_jsp_to_django/<str:input_filename>', views.convert_jsp_to_django),
    path('login/', views.login),
    path('logout/', views.logout),
    path('areas/', views.areas),
    path('areas/<int:area_pk>/', views.area),
    path('areas/<int:area_pk>/write/', views.write),
    path('update_message_path/', views.update_message_path),
    path('import_times/', views.import_times),
]
