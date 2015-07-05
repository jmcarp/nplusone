# -*- coding: utf-8 -*-

from __future__ import absolute_import

import copy
import logging
import functools

from django.conf import settings
from django.db.models import query
from django.db.models import query_utils
from django.db.models.fields import related

from nplusone.core import signals


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


def parse_single_related_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    field = descriptor.related.field
    return field.related_field.model, field.rel.related_name


def parse_reverse_single_related_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    return descriptor.field.model, descriptor.field.name


def parse_many_related_queryset(args, kwargs, context):
    manager = context['args'][0]
    return manager.instance.__class__, manager.prefetch_cache_name


def parse_foreign_related_queryset(args, kwargs, context):
    field = context['rel_field']
    return field.related_field.model, field.rel.related_name


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
            signals.get_worker(),
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
    rel = self._context['rel']
    return rel.field.model, rel.field.name


# Emit `touch` on iterating prefetched `QuerySet` instances
original_iterate_queryset = query.QuerySet.__iter__
def iterate_queryset(self):
    if self._prefetch_done:
        signals.touch.send(
            signals.get_worker(),
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
            signals.get_worker(),
            args=(self, ),
            parser=parse_iterate_queryset,
        )
    return original_getitem_queryset(self, index)
query.QuerySet.__getitem__ = getitem_queryset


class NPlusOneMiddleware(object):

    def __init__(self):
        self.logger = getattr(settings, 'NPLUSONE_LOGGER', logging.getLogger('nplusone'))
        self.level = getattr(settings, 'NPLUSONE_LOG_LEVEL', logging.DEBUG)

    def process_request(self, request):
        signals.lazy_load.connect(self.handle_lazy)
        signals.eager_load.connect(self.handle_eager)
        self.touched = set()

    def process_response(self, request, response):
        signals.lazy_load.disconnect(self.handle_lazy)
        signals.eager_load.disconnect(self.handle_eager)
        self.log_eager()
        return response

    def handle_lazy(self, caller, args, kwargs, context, parser):
        model, field = parser(args, kwargs, context)
        self.logger.log(
            self.level,
            'Potential n+1 query detected on `{0}.{1}`'.format(
                model.__name__,
                field,
            ),
        )

    def handle_eager(self, caller, args, kwargs, context, parser):
        signals.touch.connect(self.handle_touch)
        parsed = parser(args, kwargs, context)
        self.touched.add(parsed)

    def handle_touch(self, caller, args=None, kwargs=None, context=None, parser=None):
        parsed = parser(args, kwargs, context)
        if parsed in self.touched:
            self.touched.remove(parsed)

    def log_eager(self):
        for model, field in self.touched:
            self.logger.log(
                self.level,
                'Potential unnecessary eager load detected on `{0}.{1}`'.format(
                    model.__name__,
                    field,
                ),
            )
