# -*- coding: utf-8 -*-

import collections

import pytest

from nplusone.core import stack
from nplusone.core import signals


Call = collections.namedtuple('Call', ['objects', 'frame'])


@pytest.yield_fixture
def calls():
    calls = []
    def subscriber(sender, args=None, kwargs=None, context=None, parser=None):
        calls.append(
            Call(
                parser(args, kwargs, context),
                stack.get_caller(),
            )
        )
    signals.lazy_load.connect(subscriber)
    yield calls
