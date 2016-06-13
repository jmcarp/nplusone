# -*- coding: utf-8 -*-

import functools
import contextlib

import blinker


load = blinker.Signal()
ignore_load = blinker.Signal()
lazy_load = blinker.Signal()
eager_load = blinker.Signal()
touch = blinker.Signal()


def get_worker(*args, **kwargs):
    return blinker.ANY


def signalify(signal, func, parser=None, **context):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        ret = func(*args, **kwargs)
        signal.send(
            get_worker(),
            args=args,
            kwargs=kwargs,
            ret=ret,
            context=context,
            parser=parser,
        )
        return ret
    return wrapped


def designalify(signal, func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        with ignore(signal):
            return func(*args, **kwargs)
    return wrapped


@contextlib.contextmanager
def ignore(signal, sender=None):
    sender = sender or get_worker()
    receivers = list(signal.receivers_for(sender))
    for receiver in receivers:
        signal.disconnect(receiver, sender=sender)
    try:
        yield
    finally:
        for receiver in receivers:
            signal.connect(receiver, sender=sender)
