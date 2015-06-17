# -*- coding: utf-8 -*-

import copy
import logging
import functools

from django.db.models.fields import related

from nplusone.core import signals


def signalify_queryset(func, parser=None, **context):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        queryset = func(*args, **kwargs)
        ctx = copy.copy(context)
        ctx['args'] = context.get('args', args)
        ctx['kwargs'] = context.get('kwargs', kwargs)
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
    return descriptor.related.field.model, descriptor.related.field.name


def parse_reverse_single_related(args, kwargs, context):
    descriptor = context['args'][0]
    return descriptor.field.model, descriptor.field.name


def parse_many_related(args, kwargs, context):
    manager = context['args'][0]
    return manager.instance.__class__, manager.prefetch_cache_name


def parse_foreign_related(args, kwargs, context):
    field = context['rel_field']
    return field.related_model, field.rel.name


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

    def __init__(self, logger=None, level=None):
        self.logger = logger or logging.getLogger('nplusone')
        self.level = level or logging.DEBUG

    def process_request(self, request):
        signals.lazy_load.connect(self.callback)

    def process_response(self, request, response):
        signals.lazy_load.disconnect(self.callback)
        return response

    def callback(self, args, kwargs, context, parser):
        model, field = parser(args, kwargs, context)
        self.logger.log(self.level, '{0!r} : {1!r}'.format(model, field))
