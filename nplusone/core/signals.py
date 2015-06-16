# -*- coding: utf-8 -*-

import functools

import blinker


lazy_load = blinker.Signal()


def signalify(signal, func, parser=None, **context):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        signal.send(None, args=args, kwargs=kwargs, parser=parser, context=context)
        return func(*args, **kwargs)
    return wrapped
