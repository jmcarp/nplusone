# -*- coding: utf-8 -*-

import weakref

import six

from django.conf import settings

from nplusone.core import listeners
from nplusone.core import notifiers


class DjangoRule(listeners.Rule):

    def match_model(self, model):
        return (
            self.model is model or (
                isinstance(self.model, six.string_types) and
                self.model == '{0}.{1}'.format(model._meta.app_label, model.__name__)
            )
        )


class NPlusOneMiddleware(object):

    def __init__(self):
        self.listeners = weakref.WeakKeyDictionary()

    def load_config(self):
        self.notifiers = notifiers.init(vars(settings._wrapped))
        self.whitelist = [
            DjangoRule(**item)
            for item in getattr(settings, 'NPLUSONE_WHITELIST', [])
        ]

    def process_request(self, request):
        self.load_config()
        self.listeners[request] = self.listeners.get(request, {})
        for name, listener_type in six.iteritems(listeners.listeners):
            self.listeners[request][name] = listener_type(self)
            self.listeners[request][name].setup()

    def process_response(self, request, response):
        for name, listener_type in six.iteritems(listeners.listeners):
            listener = self.listeners.get(request, {}).pop(name, None)
            if listener:
                listener.teardown()
        return response

    def notify(self, message):
        if not message.match(self.whitelist):
            for notifier in self.notifiers:
                notifier.notify(message)
