import mock
import pytest
import collections

from nplusone.core import stack
from nplusone.core import signals
from nplusone.core import listeners


Call = collections.namedtuple('Call', ['objects', 'frame'])
PATTERNS = [
    'site-packages', 'py.test',
    'nplusone/core', 'nplusone/ext', 'nplusone/tests/conftest',
]


@pytest.yield_fixture
def calls():
    calls = []
    def subscriber(sender, args=None, kwargs=None, context=None, parser=None):
        calls.append(
            Call(
                parser(args, kwargs, context),
                stack.get_caller(patterns=PATTERNS)
            )
        )
    signals.lazy_load.connect(subscriber, sender=signals.get_worker())
    yield calls


@pytest.yield_fixture
def lazy_listener():
    mock_parent = mock.Mock()
    listener = listeners.LazyListener(mock_parent)
    listener.setup()
    try:
        yield listener
    finally:
        listener.teardown()
