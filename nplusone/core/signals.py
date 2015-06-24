# -*- coding: utf-8 -*-

import functools
import contextlib

import blinker


lazy_load = blinker.Signal()


def signalify(signal, func, parser=None, **context):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        signal.send(None, args=args, kwargs=kwargs, parser=parser, context=context)
        return func(*args, **kwargs)
    return wrapped


@contextlib.contextmanager
def ignore():
    receivers, lazy_load.receivers = lazy_load.receivers, {}
    try:
        yield
    finally:
        lazy_load.receivers = receivers
