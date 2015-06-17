# -*- coding: utf-8 -*-

import pytest

from nplusone.core import signals


@pytest.yield_fixture
def calls():
    calls = []
    def subscriber(sender, args=None, kwargs=None, context=None, parser=None):
        calls.append(parser(args, kwargs, context))
    signals.lazy_load.connect(subscriber)
    yield calls
