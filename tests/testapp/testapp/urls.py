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
    url(r'^many_to_many/$', views.many_to_many),
    url(r'^eager_select/$', views.eager_select),
    url(r'^eager_prefetch/$', views.eager_prefetch),
    url(r'^eager_prefetch_item/$', views.eager_prefetch_item),
    url(r'^eager_select_unused/$', views.eager_select_unused),
    url(r'^eager_prefetch_scalar/$', views.eager_prefetch_scalar),
    url(r'^eager_prefetch_scalar_unused/$', views.eager_prefetch_scalar_unused),
]
