from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^one_to_one/$', views.one_to_one),
    url(r'^one_to_one_first/$', views.one_to_one_first),
    url(r'^one_to_many/$', views.one_to_many),
    url(r'^many_to_many/$', views.many_to_many),
    url(r'^many_to_many_get/$', views.many_to_many_get),
    url(r'^prefetch_one_to_one/$', views.prefetch_one_to_one),
    url(r'^prefetch_one_to_one_unused/$', views.prefetch_one_to_one_unused),
    url(r'^prefetch_many_to_many/$', views.prefetch_many_to_many),
    url(r'^many_to_many_impossible/$', views.many_to_many_impossible),
    url(r'^many_to_many_impossible_one/$', views.many_to_many_impossible_one),
    url(r'^prefetch_many_to_many_render/$', views.prefetch_many_to_many_render),
    url(r'^prefetch_many_to_many_unused/$', views.prefetch_many_to_many_unused),
    url(r'^prefetch_many_to_many_single/$', views.prefetch_many_to_many_single),
    url(r'^prefetch_many_to_many_no_related/$', views.prefetch_many_to_many_no_related),
    url(r'^select_one_to_one/$', views.select_one_to_one),
    url(r'^select_one_to_one_unused/$', views.select_one_to_one_unused),
    url(r'^select_many_to_one/$', views.select_many_to_one),
    url(r'^select_many_to_one_unused/$', views.select_many_to_one_unused),
    url(r'^prefetch_nested/$', views.prefetch_nested),
    url(r'^prefetch_nested_unused/$', views.prefetch_nested_unused),
    url(r'^select_nested/$', views.select_nested),
    url(r'^select_nested_unused/$', views.select_nested_unused),
    url(r'^deferred/$', views.deferred),
    url(r'^double_deferred/$', views.double_deferred),
]
