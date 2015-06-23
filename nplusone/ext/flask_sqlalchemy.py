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
            signals.lazy_load.connect(self.callback)

        @self.app.teardown_request
        def disconnect(error=None):
            signals.lazy_load.disconnect(self.callback)

    def callback(self, caller, args, kwargs, context, parser):
        model, field = parser(args, kwargs, context)
        self.logger.log(
            self.level,
            'Potential n+1 query detected on `{0}.{1}`'.format(
                model.__name__,
                field,
            ),
        )
