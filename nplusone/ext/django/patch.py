# -*- coding: utf-8 -*-

import copy
import inspect
import functools
import importlib
import threading

import django
from django.db.models import query
from django.db.models import query_utils

from nplusone.core import signals

if django.VERSION >= (1, 9):  # pragma: no cover
    from django.db.models.fields.related_descriptors import (
        ReverseOneToOneDescriptor,
        ForwardManyToOneDescriptor,
        create_reverse_many_to_one_manager,
        create_forward_many_to_many_manager,
    )
else:  # pragma: no cover
    from django.db.models.fields.related import (
        SingleRelatedObjectDescriptor as ReverseOneToOneDescriptor,
        ReverseSingleRelatedObjectDescriptor as ForwardManyToOneDescriptor,
        create_foreign_related_manager as create_reverse_many_to_one_manager,
        create_many_related_manager as create_forward_many_to_many_manager,
    )


def get_worker():
    return str(threading.current_thread().ident)


def setup_state():
    signals.get_worker = get_worker
setup_state()


def patch(original, patched):
    module = importlib.import_module(original.__module__)
    setattr(module, original.__name__, patched)


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


def get_related_name(model):
    return '{0}_set'.format(model._meta.model_name)


def parse_field(field):
    return (
        (
            field.rel.model  # Django >= 1.8
            if hasattr(field.rel, 'model')
            else field.related_field.model  # Django <= 1.8
        ),
        field.rel.related_name,
    )


def parse_related(context):
    if 'rel' in context:  # pragma: no cover
        rel = context['rel']
        return parse_related_parts(rel.model, rel.related_name, rel.related_model)
    else:  # pragma: no cover
        field = context['rel_field']
        model = field.related_field.model
        related_name = field.rel.related_name
        related_model = context['rel_model']
        return parse_related_parts(model, related_name, related_model)


def parse_related_parts(model, related_name, related_model):
    return (
        model,
        related_name or get_related_name(related_model),
    )


def parse_reverse_one_to_one_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    field = descriptor.related.field
    return parse_field(field)


def parse_forward_many_to_one_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    return descriptor.field.model, descriptor.field.name


def parse_many_related_queryset(args, kwargs, context):
    rel = context['rel']
    manager = context['args'][0]
    model = manager.instance.__class__
    related_model = (
        manager.target_field.related_model  # Django >= 1.8
        if hasattr(manager.target_field, 'related_model')
        else manager.target_field.related_field.model  # Django <= 1.8
    )
    field = manager.prefetch_cache_name if rel.related_name else None
    return (
        model,
        field or get_related_name(related_model),
    )


def parse_foreign_related_queryset(args, kwargs, context):
    return parse_related(context)


query.prefetch_one_level = signals.designalify(
    signals.lazy_load,
    query.prefetch_one_level,
)


ReverseOneToOneDescriptor.get_queryset = signalify_queryset(
    ReverseOneToOneDescriptor.get_queryset,
    parser=parse_reverse_one_to_one_queryset,
)
ForwardManyToOneDescriptor.get_queryset = signalify_queryset(
    ForwardManyToOneDescriptor.get_queryset,
    parser=parse_forward_many_to_one_queryset,
)


def _create_forward_many_to_many_manager(*args, **kwargs):
    context = inspect.getcallargs(create_forward_many_to_many_manager, *args, **kwargs)
    manager = create_forward_many_to_many_manager(*args, **kwargs)
    manager.get_queryset = signalify_queryset(
        manager.get_queryset,
        parser=parse_many_related_queryset,
        **context
    )
    return manager
patch(create_forward_many_to_many_manager, _create_forward_many_to_many_manager)


def _create_reverse_many_to_one_manager(*args, **kwargs):
    context = inspect.getcallargs(create_reverse_many_to_one_manager, *args, **kwargs)
    manager = create_reverse_many_to_one_manager(*args, **kwargs)

    manager.get_queryset = signalify_queryset(
        manager.get_queryset,
        parser=parse_foreign_related_queryset,
        **context
    )
    return manager
patch(create_reverse_many_to_one_manager, _create_reverse_many_to_one_manager)


def parse_get_prefetcher(args, kwargs, context):
    instance, field = args
    return instance.__class__, field


def parse_select_related(args, kwargs, context):
    field = args[0]
    return parse_field(field)


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


def parse_reverse_one_to_one_get(args, kwargs, context):
    descriptor, instance = args[:2]
    if instance is None:
        return None
    field = descriptor.related.field
    return parse_field(field)


ReverseOneToOneDescriptor.__get__ = signals.signalify(
    signals.touch,
    ReverseOneToOneDescriptor.__get__,
    parser=parse_reverse_one_to_one_get,
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
            return parse_related(self._context)


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
