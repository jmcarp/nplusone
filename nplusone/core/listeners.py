# -*- coding: utf-8 -*-

import six
from collections import defaultdict

from nplusone.core import signals


class Rule(object):

    def __init__(self, label=None, model=None, field=None):
        self.label = label
        self.model = model
        self.field = field

    def compare(self, label, model, field):
        return (
            (self.label or self.model or self.field) and
            (self.label is None or self.label == label) and
            (self.model is None or self.match_model(model)) and
            (self.field is None or self.field == field)
        )

    def match_model(self, model):
        return (
            self.model is model or (
                isinstance(self.model, six.string_types) and
                self.model == model.__name__
            )
        )


class Message(object):

    label = ''
    formatter = ''

    def __init__(self, model, field):
        self.model = model
        self.field = field

    @property
    def message(self):
        return self.formatter.format(
            label=self.label,
            model=self.model.__name__,
            field=self.field,
        )

    def match(self, rules):
        return any(
            rule.compare(self.label, self.model, self.field)
            for rule in rules
        )


class LazyLoadMessage(Message):
    label = 'n_plus_one'
    formatter = 'Potential n+1 query detected on `{model}.{field}`'


class EagerLoadMessage(Message):
    label = 'unused_eager_load'
    formatter = 'Potential unnecessary eager load detected on `{model}.{field}`'


class Listener(object):

    def __init__(self, parent):
        self.parent = parent

    def setup(self):
        pass  # pragma: no cover

    def teardown(self):
        pass  # pragma: no cover


class LazyListener(Listener):

    def setup(self):
        self.loaded = set()
        signals.load.connect(self.handle_load, sender=signals.get_worker())
        signals.lazy_load.connect(self.handle_lazy, sender=signals.get_worker())

    def handle_load(self, caller, args=None, kwargs=None, context=None, ret=None,
                    parser=None):
        instances = parser(args, kwargs, context, ret)
        self.loaded.update(instances)

    def handle_lazy(self, caller, args=None, kwargs=None, context=None, parser=None):
        model, instance, field = parser(args, kwargs, context)
        if instance in self.loaded:
            message = LazyLoadMessage(model, field)
            self.parent.notify(message)


class EagerListener(Listener):

    def setup(self):
        signals.eager_load.connect(self.handle_eager, sender=signals.get_worker())
        self._get_instances = None
        self.fetched = []
        self.touched = []

    def teardown(self):
        self.log_eager()

    def handle_eager(self, caller, args=None, kwargs=None, context=None, parser=None):
        self.fetched.append(parser(args, kwargs, context))
        signals.touch.connect(self.handle_touch, sender=signals.get_worker())

    def handle_touch(self, caller, args=None, kwargs=None, context=None, parser=None):
        res = parser(args, kwargs, context)
        if res:
            self.touched.append(res)

    def log_eager(self):
        groups = defaultdict(lambda: defaultdict(set))
        for model, field, instances, key in self.fetched:
            groups[(model, field)][id(key)].update(instances)
        for model, field, instance in self.touched:
            group = groups[(model, field)]
            for key, instances in list(group.items()):
                if instance and instances.intersection(instance) and key in group:
                    group.pop(key)
        for (model, field), group in groups.items():
            if group:
                message = EagerLoadMessage(model, field)
                self.parent.notify(message)


listeners = {
    'lazy_load': LazyListener,
    'eager_load': EagerListener,
}
