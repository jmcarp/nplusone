# -*- coding: utf-8 -*-

from nplusone.core import profiler


class NPlusOneMiddleware(object):

    def __init__(self, app, whitelist=None):
        self.app = app
        self.whitelist = whitelist

    def __call__(self, environ, start_response):
        with profiler.Profiler(whitelist=self.whitelist):
            return self.app(environ, start_response)
