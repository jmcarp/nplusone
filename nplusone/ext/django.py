# -*- coding: utf-8 -*-

from __future__ import absolute_import

import copy
import weakref
import functools
import threading

import six

from django.conf import settings
from django.db.models import query
from django.db.models import query_utils
from django.db.models.fields import related

from nplusone.core import signals
from nplusone.core import listeners
from nplusone.core import notifiers


def get_worker():
    return str(threading.current_thread().ident)


def setup_state():
    signals.get_worker = get_worker
setup_state()


def signalify_queryset(func, parser=None, **context):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        queryset = func(*args, **kwargs)
        ctx = copy.copy(context)
        ctx['args'] = context.get('args', args)
        ctx['kwargs'] = context.get('kwargs', kwargs)
        # In Django 1.7.x, some `get_queryset` methods return a `Manager`, not a
        # `QuerySet`; in this case, patch the `get_queryset` method of the returned
        # `Manager`.
        if hasattr(queryset, 'get_queryset'):  # pragma: no cover
            queryset.get_queryset = signalify_queryset(
                queryset.get_queryset,
                parser=parser,
                **ctx
            )
        else:
            queryset._clone = signalify_queryset(queryset._clone, parser=parser, **ctx)
            queryset.iterator = signals.signalify(
                signals.lazy_load,
                queryset.iterator,
                parser=parser,
                **ctx
            )
            queryset._context = ctx
        return queryset
    return wrapped


def related_name(model):
    return '{0}_set'.format(model._meta.model_name)


def parse_single_related_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    field = descriptor.related.field
    return field.related_field.model, field.rel.related_name


def parse_reverse_single_related_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    return descriptor.field.model, descriptor.field.name


def parse_many_related_queryset(args, kwargs, context):
    rel = context['rel']
    manager = context['args'][0]
    model = manager.instance.__class__
    related_model = manager.target_field.related_field.model
    field = manager.prefetch_cache_name if rel.related_name else None
    return (
        model,
        field or related_name(related_model),
    )


def parse_foreign_related_queryset(args, kwargs, context):
    field = context['rel_field']
    related_model = context['rel_model']
    return (
        field.related_field.model,
        field.rel.related_name or related_name(related_model),
    )


query.prefetch_one_level = signals.designalify(
    signals.lazy_load,
    query.prefetch_one_level,
)


related.SingleRelatedObjectDescriptor.get_queryset = signalify_queryset(
    related.SingleRelatedObjectDescriptor.get_queryset,
    parser=parse_single_related_queryset,
)
related.ReverseSingleRelatedObjectDescriptor.get_queryset = signalify_queryset(
    related.ReverseSingleRelatedObjectDescriptor.get_queryset,
    parser=parse_reverse_single_related_queryset,
)


original_create_many_related_manager = related.create_many_related_manager
def create_many_related_manager(superclass, rel):
    manager = original_create_many_related_manager(superclass, rel)
    manager.get_queryset = signalify_queryset(
        manager.get_queryset,
        parser=parse_many_related_queryset,
        rel=rel,
    )
    return manager
related.create_many_related_manager = create_many_related_manager


original_create_foreign_related_manager = related.create_foreign_related_manager
def create_foreign_related_manager(superclass, rel_field, rel_model):
    manager = original_create_foreign_related_manager(superclass, rel_field, rel_model)
    manager.get_queryset = signalify_queryset(
        manager.get_queryset,
        parser=parse_foreign_related_queryset,
        rel_field=rel_field,
        rel_model=rel_model,
    )
    return manager
related.create_foreign_related_manager = create_foreign_related_manager


def parse_get_prefetcher(args, kwargs, context):
    instance, field = args
    return instance.__class__, field


def parse_select_related(args, kwargs, context):
    field = args[0]
    return field.related_field.model, field.rel.related_name


query.get_prefetcher = signals.signalify(
    signals.eager_load,
    query.get_prefetcher,
    parser=parse_get_prefetcher,
)


# Emit `eager_load` on verified `select_related_descend`
original_select_related_descend = query_utils.select_related_descend
def select_related_descend(*args, **kwargs):
    ret = original_select_related_descend(*args, **kwargs)
    if ret:
        signals.eager_load.send(
            get_worker(),
            args=args,
            kwargs=kwargs,
            parser=parse_select_related,
            context=None,
        )
    return ret
query_utils.select_related_descend = select_related_descend


def parse_single_related_get(args, kwargs, context):
    descriptor, instance = args[:2]
    if instance is None:
        return None
    field = descriptor.related.field
    return field.related_field.model, field.rel.related_name


related.SingleRelatedObjectDescriptor.__get__ = signals.signalify(
    signals.touch,
    related.SingleRelatedObjectDescriptor.__get__,
    parser=parse_single_related_get,
)


def parse_iterate_queryset(args, kwargs, context):
    self = args[0]
    if hasattr(self, '_context'):
        manager = self._context['args'][0]
        # Handle iteration over many-to-many relationship
        if manager.__class__.__name__ == 'ManyRelatedManager':
            return manager.instance.__class__, manager.prefetch_cache_name
        # Handle iteration over one-to-many relationship
        else:
            related_field = self._context['rel_field']
            return manager.instance.__class__, related_field.rel.related_name


# Emit `touch` on iterating prefetched `QuerySet` instances
original_iterate_queryset = query.QuerySet.__iter__
def iterate_queryset(self):
    if self._prefetch_done:
        signals.touch.send(
            get_worker(),
            args=(self, ),
            parser=parse_iterate_queryset,
        )
    return original_iterate_queryset(self)
query.QuerySet.__iter__ = iterate_queryset


# Emit `touch` on indexing into prefetched `QuerySet` instances
original_getitem_queryset = query.QuerySet.__getitem__
def getitem_queryset(self, index):
    if self._prefetch_done:
        signals.touch.send(
            get_worker(),
            args=(self, ),
            parser=parse_iterate_queryset,
        )
    return original_getitem_queryset(self, index)
query.QuerySet.__getitem__ = getitem_queryset


class NPlusOneMiddleware(object):

    def __init__(self):
        self.notifiers = notifiers.init(vars(settings._wrapped))
        self.listeners = weakref.WeakKeyDictionary()

    def process_request(self, request):
        self.listeners[request] = self.listeners.get(request, {})
        for name, listener_type in six.iteritems(listeners.listeners):
            self.listeners[request][name] = listener_type(self)
            self.listeners[request][name].setup()

    def process_response(self, request, response):
        for name, listener_type in six.iteritems(listeners.listeners):
            listener = self.listeners[request].pop(name)
            listener.teardown()
        return response

    def notify(self, message):
        for notifier in self.notifiers:
            notifier.notify(message)
