# -*- coding: utf-8 -*-

import copy
import inspect
import functools
import importlib
import threading

import django
from django.db.models import query
from django.db.models import Model

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


def to_key(instance):
    model = type(instance)
    return ':'.join([model.__name__, format(instance.pk)])


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
        queryset._clone = signalify_queryset(queryset._clone, parser=parser, **ctx)
        queryset._fetch_all = signalify_fetch_all(queryset, parser=parser, **ctx)
        queryset._context = ctx
        return queryset
    return wrapped


def signalify_fetch_all(queryset, parser=None, **context):
    """Signal lazy load when `QuerySet._fetch_all` fetches rows. Note: patch
    `_fetch_all` instead of `iterator` since, as of Django 1.11, the former is
    used for all fetches while the latter is not.
    """
    func = queryset._fetch_all
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if queryset._result_cache is None:
            signals.lazy_load.send(
                get_worker(),
                args=args,
                kwargs=kwargs,
                ret=None,
                context=context,
                parser=parser,
            )
        return func(*args, **kwargs)
    return wrapped


def get_related_name(model):
    return '{0}_set'.format(model._meta.model_name)


def parse_field(field):
    return (
        (
            field.related_model  # Django >= 1.8
            if hasattr(field, 'related_model')
            else field.related_field.model  # Django <= 1.8
        ),
        (
            field.remote_field.name  # Django >= 1.8
            if hasattr(field, 'remote_field')
            else field.rel.related_name  # Django <= 1.8
        ) or get_related_name(field.related_model),
    )


def parse_reverse_field(field):
    return field.model, field.name


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
    model, name = parse_field(field)
    instance = context['kwargs']['instance']
    return model, to_key(instance), name


def parse_forward_many_to_one_queryset(args, kwargs, context):
    descriptor = context['args'][0]
    instance = context['kwargs']['instance']
    return descriptor.field.model, to_key(instance), descriptor.field.name


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
        to_key(manager.instance),
        field or get_related_name(related_model),
    )


def parse_foreign_related_queryset(args, kwargs, context):
    model, name = parse_related(context)
    descriptor = context['args'][0]
    return model, to_key(descriptor.instance), name


query.prefetch_one_level = signals.designalify(
    signals.lazy_load,
    query.prefetch_one_level,
)


def parse_get(args, kwargs, context, ret):
    return [to_key(ret)] if isinstance(ret, Model) else []


# Ignore records loaded during `get`
query.QuerySet.get = signals.signalify(
    signals.ignore_load,
    query.QuerySet.get,
    parser=parse_get,
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


def parse_forward_many_to_one_get(args, kwargs, context):
    descriptor, instance, _ = args
    if instance is None:
        return None
    field, model = parse_reverse_field(descriptor.field)
    return field, model, [to_key(instance)]


ForwardManyToOneDescriptor.__get__ = signals.signalify(
    signals.touch,
    ForwardManyToOneDescriptor.__get__,
    parser=parse_forward_many_to_one_get,
)


def parse_reverse_one_to_one_get(args, kwargs, context):
    descriptor, instance = args[:2]
    if instance is None:
        return None
    model, field = parse_field(descriptor.related.field)
    return model, field, [to_key(instance)]


ReverseOneToOneDescriptor.__get__ = signals.signalify(
    signals.touch,
    ReverseOneToOneDescriptor.__get__,
    parser=parse_reverse_one_to_one_get,
)


def parse_fetch_all(args, kwargs, context):
    self = args[0]
    if hasattr(self, '_context'):
        manager = self._context['args'][0]
        instance = manager.instance
        # Handle iteration over many-to-many relationship
        if manager.__class__.__name__ == 'ManyRelatedManager':
            return (
                instance.__class__,
                parse_manager_field(manager, self._context['rel']),
                [to_key(instance)],
            )
        # Handle iteration over one-to-many relationship
        else:
            model, field = parse_related(self._context)
            return model, field, [to_key(instance)]


def parse_manager_field(manager, rel):
    if manager.reverse:
        return rel.related_name or get_related_name(rel.related_model)
    return rel.field.name or get_related_name(rel.model)


def parse_load(args, kwargs, context, ret):
    return [
        to_key(row)
        for row in ret
        if isinstance(row, Model)
    ]


def is_single(low, high):
    return high is not None and high - low == 1


# On queryset fetch, emit `touch` if results have been prefetched; emit `load`
# if the query requests more than one record, else `ignore_load`. Note: we patch
# `_fetch_all` rather than `__iter__` to handle iteration over empty querysets
# in Django templates, which does not call `__iter__`.
original_fetch_all = query.QuerySet._fetch_all
def fetch_all(self):
    if self._prefetch_done:
        signals.touch.send(
            get_worker(),
            args=(self, ),
            parser=parse_fetch_all,
        )
    original_fetch_all(self)
    signal = (
        signals.ignore_load
        if is_single(self.query.low_mark, self.query.high_mark)
        else signals.load
    )
    signal.send(
        get_worker(),
        args=(self, ),
        ret=self._result_cache,
        parser=parse_load,
    )
query.QuerySet._fetch_all = fetch_all


original_related_populator_init = query.RelatedPopulator.__init__
def related_populator_init(self, *args, **kwargs):
    original_related_populator_init(self, *args, **kwargs)
    self.__nplusone__ = {
        'args': args,
        'kwargs': kwargs,
    }
query.RelatedPopulator.__init__ = related_populator_init


def parse_eager_select(args, kwargs, context):
    populator = args[0]
    instance = args[2]
    meta = populator.__nplusone__
    klass_info, select, _ = meta['args']
    field = klass_info['field']
    model, name = (
        parse_field(field)
        if instance._meta.model != field.model
        else parse_reverse_field(field)
    )
    return model, name, [to_key(instance)], id(select)


# Emit `eager_load` on populating from `select_related`
query.RelatedPopulator.populate = signals.signalify(
    signals.eager_load,
    query.RelatedPopulator.populate,
    parser=parse_eager_select,
)


def parse_eager_join(args, kwargs, context):
    instances, descriptor, fetcher, level = args
    model = instances[0].__class__
    field, _ = fetcher.get_current_to_attr(level)
    keys = [to_key(instance) for instance in instances]
    return model, field, keys, id(instances)


# Emit `eager_load` on populating from `prefetch_related`
query.prefetch_one_level = signals.signalify(
    signals.eager_load,
    query.prefetch_one_level,
    parser=parse_eager_join,
)


# Emit `touch` on indexing into prefetched `QuerySet` instances
original_getitem_queryset = query.QuerySet.__getitem__
def getitem_queryset(self, index):
    if self._prefetch_done:
        signals.touch.send(
            get_worker(),
            args=(self, ),
            parser=parse_fetch_all,
        )
    return original_getitem_queryset(self, index)
query.QuerySet.__getitem__ = getitem_queryset
