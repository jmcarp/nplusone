# -*- coding: utf-8 -*-

import six

from nplusone.core import listeners
from nplusone.core import exceptions


class Profiler(object):

    def __init__(self, whitelist=None):
        self.whitelist = [
            listeners.Rule(**item)
            for item in (whitelist or [])
        ]

    def __enter__(self):
        self.listeners = {}
        for name, listener_type in six.iteritems(listeners.listeners):
            self.listeners[name] = listener_type(self)
            self.listeners[name].setup()

    def __exit__(self, *exc):
        for name in six.iterkeys(listeners.listeners):
            self.listeners.pop(name).teardown()

    def notify(self, message):
        if not message.match(self.whitelist):
            raise exceptions.NPlusOneError(message.message)
