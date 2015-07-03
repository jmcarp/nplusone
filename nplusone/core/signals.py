# -*- coding: utf-8 -*-

import functools
import contextlib

import blinker


lazy_load = blinker.Signal()
eager_load = blinker.Signal()
touch = blinker.Signal()


noop = lambda *a, **kw: None


def signalify(signal, func, sender=None, parser=None, **context):
    sender = sender or noop
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        signal.send(
            sender(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            context=context,
            parser=parser,
        )
        return func(*args, **kwargs)
    return wrapped


@contextlib.contextmanager
def ignore():
    receivers, lazy_load.receivers = lazy_load.receivers, {}
    try:
        yield
    finally:
        lazy_load.receivers = receivers
