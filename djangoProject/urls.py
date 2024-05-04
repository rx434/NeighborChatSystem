"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from .views import user_login, register, logout
from .home import home, profile, address, serve_media
from .block import block, neighbor, follow
from .apply import apply, approve, cancel, leave
from .relation import relation, neighbor_relation, friend_relation, cancel_application, approve_friend
from .message import message, view_message
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('profile/<int:uid>/', profile, name='profile'),
    path('address/', address, name='address'),
    path('block/<int:bid>/', block, name='block'),
    path('neighbor/<int:nid>/', neighbor, name='neighbor'),
    path('media/<path:path>/', serve_media, name='serve_media'),
    path('apply/', apply, name='apply'),
    path('follow/', follow, name='follow'),
    path('approve/', approve, name='approve'),
    path('cancel/', cancel, name='cancel'),
    path('leave/', leave, name='leave'),
    path('relation/', relation, name='relation'),
    path('neighbor_relation/', neighbor_relation, name='neighbor_relation'),
    path('friend_relation/', friend_relation, name='friend_relation'),
    path('cancel_application/', cancel_application, name='cancel_application'),
    path('approve_friend/', approve_friend, name='approve_friend'),
    path('message/<int:mid>/', message, name='message'),
    path('view_message/', view_message, name='view_message')
    # Include other paths as necessary
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
