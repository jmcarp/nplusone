# -*- coding: utf-8 -*-

import six
from flask import g
from flask import request

from nplusone.core import signals
from nplusone.core import listeners
from nplusone.core import notifiers
import nplusone.ext.sqlalchemy  # noqa


def get_worker():
    try:
        return request._get_current_object()
    except RuntimeError:
        return None


def setup_state():
    signals.get_worker = get_worker
setup_state()


class NPlusOne(object):

    def __init__(self, app):
        self.app = app
        self.notifiers = notifiers.init(self.app.config)
        self.init_app()

    def init_app(self):
        @self.app.before_request
        def connect():
            g.listeners = getattr(g, 'listeners', {})
            for name, listener_type in six.iteritems(listeners.listeners):
                g.listeners[name] = listener_type(self)
                g.listeners[name].setup()

        @self.app.after_request
        def disconnect(response):
            for name, listener_type in six.iteritems(listeners.listeners):
                listener = g.listeners.pop(name)
                listener.teardown()
            return response

    def notify(self, message):
        for notifier in self.notifiers:
            notifier.notify(message)
