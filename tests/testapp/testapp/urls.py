"""testapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^one_to_one/$', views.one_to_one),
    url(r'^one_to_one_first/$', views.one_to_one_first),
    url(r'^one_to_many/$', views.one_to_many),
    url(r'^many_to_many/$', views.many_to_many),
    url(r'^prefetch_one_to_one/$', views.prefetch_one_to_one),
    url(r'^prefetch_one_to_one_unused/$', views.prefetch_one_to_one_unused),
    url(r'^prefetch_many_to_many/$', views.prefetch_many_to_many),
    url(r'^prefetch_many_to_many_unused/$', views.prefetch_many_to_many_unused),
    url(r'^prefetch_many_to_many_single/$', views.prefetch_many_to_many_single),
    url(r'^select_one_to_one/$', views.select_one_to_one),
    url(r'^select_one_to_one_unused/$', views.select_one_to_one_unused),
]
