# -*- coding: utf-8 -*-

import six
import fnmatch
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
                fnmatch.fnmatch(model.__name__, self.model)
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
        self.loaded, self.ignore = set(), set()
        signals.load.connect(self.handle_load, sender=signals.get_worker())
        signals.ignore_load.connect(self.handle_ignore, sender=signals.get_worker())
        signals.lazy_load.connect(self.handle_lazy, sender=signals.get_worker())

    def handle_load(self, caller, args=None, kwargs=None, context=None, ret=None,
                    parser=None):
        instances = parser(args, kwargs, context, ret)
        self.loaded.update(instances)

    def handle_ignore(self, caller, args=None, kwargs=None, context=None, ret=None,
                      parser=None):
        instances = parser(args, kwargs, context, ret)
        self.ignore.update(instances)

    def handle_lazy(self, caller, args=None, kwargs=None, context=None, ret=None,
                    parser=None):
        model, instance, field = parser(args, kwargs, context)
        if instance in self.loaded and instance not in self.ignore:
            message = LazyLoadMessage(model, field)
            self.parent.notify(message)


class EagerListener(Listener):

    def setup(self):
        signals.eager_load.connect(self.handle_eager, sender=signals.get_worker())
        self.tracker = EagerTracker()
        self.touched = []

    def teardown(self):
        self.log_eager()

    def handle_eager(self, caller, args=None, kwargs=None, context=None, ret=None,
                     parser=None):
        self.tracker.track(*parser(args, kwargs, context))
        signals.touch.connect(self.handle_touch, sender=signals.get_worker())

    def handle_touch(self, caller, args=None, kwargs=None, context=None, ret=None,
                     parser=None):
        self.touched.append(parser(args, kwargs, context))

    def log_eager(self):
        self.tracker.prune([each for each in self.touched if each])
        for model, field in self.tracker.unused:
            message = EagerLoadMessage(model, field)
            self.parent.notify(message)


class EagerTracker(object):
    """Data structure for tracking eager-loaded and subsequently touched
    related rows. Eager-loaded rows are stored in a dict mapping associations
    to nested dicts mapping query keys to instances.
    """
    def __init__(self):
        self.data = defaultdict(lambda: defaultdict(set))

    def track(self, model, field, instances, key):
        self.data[(model, field)][key].update(instances)

    def prune(self, touched):
        for model, field, touch_instances in touched:
            group = self.data[(model, field)]
            for key, fetch_instances in list(group.items()):
                if touch_instances and fetch_instances.intersection(touch_instances):
                    group.pop(key, None)

    @property
    def unused(self):
        return [
            (model, field)
            for (model, field), group in self.data.items()
            if group
        ]


listeners = {
    'lazy_load': LazyListener,
    'eager_load': EagerListener,
}
