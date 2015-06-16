# -*- coding: utf-8 -*-

from sqlalchemy.orm.strategies import LazyLoader

from nplusone.core import signals


def parse_lazy_load(args, kwargs, context):
    loader = args[0]
    return loader.parent.class_, loader.parent_property.key


LazyLoader._load_for_state = signals.signalify(
    signals.lazy_load,
    LazyLoader._load_for_state,
    parser=parse_lazy_load,
)
