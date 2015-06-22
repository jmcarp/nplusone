# -*- coding: utf-8 -*-

from __future__ import absolute_import

import copy
import logging
import functools

from django.conf import settings
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
        return queryset
    return wrapped


def parse_single_related(args, kwargs, context):
    descriptor = context['args'][0]
    field = descriptor.related.field
    return field.related_field.model, field.rel.related_name


def parse_reverse_single_related(args, kwargs, context):
    descriptor = context['args'][0]
    return descriptor.field.model, descriptor.field.name


def parse_many_related(args, kwargs, context):
    manager = context['args'][0]
    return manager.instance.__class__, manager.prefetch_cache_name


def parse_foreign_related(args, kwargs, context):
    field = context['rel_field']
    return field.related_field.model, field.rel.related_name


related.SingleRelatedObjectDescriptor.get_queryset = signalify_queryset(
    related.SingleRelatedObjectDescriptor.get_queryset,
    parser=parse_single_related,
)
related.ReverseSingleRelatedObjectDescriptor.get_queryset = signalify_queryset(
    related.ReverseSingleRelatedObjectDescriptor.get_queryset,
    parser=parse_reverse_single_related,
)


original_create_many_related_manager = related.create_many_related_manager
def create_many_related_manager(superclass, rel):
    manager = original_create_many_related_manager(superclass, rel)
    manager.get_queryset = signalify_queryset(
        manager.get_queryset,
        parser=parse_many_related,
        rel=rel,
    )
    return manager
related.create_many_related_manager = create_many_related_manager


original_create_foreign_related_manager = related.create_foreign_related_manager
def create_foreign_related_manager(superclass, rel_field, rel_model):
    manager = original_create_foreign_related_manager(superclass, rel_field, rel_model)
    manager.get_queryset = signalify_queryset(
        manager.get_queryset,
        parser=parse_foreign_related,
        rel_field=rel_field,
        rel_model=rel_model,
    )
    return manager
related.create_foreign_related_manager = create_foreign_related_manager


class NPlusOneMiddleware(object):

    def __init__(self):
        self.logger = getattr(settings, 'NPLUSONE_LOGGER', logging.getLogger('nplusone'))
        self.level = getattr(settings, 'NPLUSONE_LOG_LEVEL', logging.DEBUG)

    def process_request(self, request):
        signals.lazy_load.connect(self.callback)

    def process_response(self, request, response):
        signals.lazy_load.disconnect(self.callback)
        return response

    def callback(self, caller, args, kwargs, context, parser):
        model, field = parser(args, kwargs, context)
        self.logger.log(
            self.level,
            'Potential n+1 query detected on `{0}.{1}`'.format(
                model.__name__,
                field,
            ),
        )
