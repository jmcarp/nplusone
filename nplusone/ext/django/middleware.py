# -*- coding: utf-8 -*-

import weakref

import six

from django.conf import settings

from nplusone.core import listeners
from nplusone.core import notifiers


class NPlusOneMiddleware(object):

    def __init__(self):
        self.notifiers = notifiers.init(vars(settings._wrapped))
        self.listeners = weakref.WeakKeyDictionary()

    def process_request(self, request):
        self.listeners[request] = self.listeners.get(request, {})
        for name, listener_type in six.iteritems(listeners.listeners):
            self.listeners[request][name] = listener_type(self)
            self.listeners[request][name].setup()

    def process_response(self, request, response):
        for name, listener_type in six.iteritems(listeners.listeners):
            listener = self.listeners[request].pop(name)
            listener.teardown()
        return response

    def notify(self, message):
        for notifier in self.notifiers:
            notifier.notify(message)
