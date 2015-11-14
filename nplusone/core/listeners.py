# -*- coding: utf-8 -*-

from nplusone.core import signals


class Listener(object):

    def __init__(self, parent):
        self.parent = parent

    def setup(self):
        pass  # pragma: no cover

    def teardown(self):
        pass  # pragma: no cover


class LazyListener(Listener):

    def setup(self):
        signals.lazy_load.connect(self.handle_lazy, sender=signals.get_worker())

    def handle_lazy(self, caller, args=None, kwargs=None, context=None, parser=None):
        model, field = parser(args, kwargs, context)
        self.parent.notify(
            'Potential n+1 query detected on `{0}.{1}`'.format(
                model.__name__,
                field,
            ),
        )


class EagerListener(Listener):

    def setup(self):
        signals.eager_load.connect(self.handle_eager, sender=signals.get_worker())
        self.touched = set()

    def teardown(self):
        self.log_eager()

    def handle_eager(self, caller, args=None, kwargs=None, context=None, parser=None):
        signals.touch.connect(self.handle_touch, sender=signals.get_worker())
        parsed = parser(args, kwargs, context)
        self.touched.add(parsed)

    def handle_touch(self, caller, args=None, kwargs=None, context=None, parser=None):
        parsed = parser(args, kwargs, context)
        if parsed in self.touched:
            self.touched.remove(parsed)

    def log_eager(self):
        for model, field in self.touched:
            self.parent.notify(
                'Potential unnecessary eager load detected on `{0}.{1}`'.format(
                    model.__name__,
                    field,
                ),
            )


listeners = {
    'lazy_load': LazyListener,
    'eager_load': EagerListener,
}
