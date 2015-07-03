# -*- coding: utf-8 -*-

import logging

from nplusone.core import signals
import nplusone.ext.sqlalchemy  # noqa


class NPlusOne(object):

    def __init__(self, app):
        self.app = app
        config = self.app.config
        self.logger = config.get('NPLUSONE_LOGGER', logging.getLogger('nplusone'))
        self.level = config.get('NPLUSONE_LOG_LEVEL', logging.DEBUG)
        self.init_app()

    def init_app(self):
        @self.app.before_request
        def connect():
            signals.lazy_load.connect(self.handle_lazy)
            signals.eager_load.connect(self.handle_eager)
            self.touched = set()

        @self.app.teardown_request
        def disconnect(error=None):
            signals.lazy_load.disconnect(self.handle_lazy)
            signals.eager_load.disconnect(self.handle_eager)
            signals.touch.disconnect(self.handle_touch)
            self.log_eager()

    def handle_lazy(self, caller, args, kwargs, context, parser):
        model, field = parser(args, kwargs, context)
        self.logger.log(
            self.level,
            'Potential n+1 query detected on `{0}.{1}`'.format(
                model.__name__,
                field,
            ),
        )

    def handle_eager(self, caller, args, kwargs, context, parser):
        model, field = parser(args, kwargs, context)
        attr = getattr(model, field)
        signals.touch.connect(self.handle_touch, sender=attr)
        self.touched.add(attr)

    def handle_touch(self, caller, args, kwargs, context, parser):
        self.touched.remove(caller)

    def log_eager(self):
        for attr in self.touched:
            self.logger.log(
                self.level,
                'Potential unnecessary eager load detected on `{0}.{1}`'.format(
                    attr.class_.__name__,
                    attr.key,
                ),
            )
