# -*- coding: utf-8 -*-

import inspect

PATTERNS = ['site-packages', 'py.test', 'nplusone']


def get_caller(patterns=None):
    frames = inspect.stack()
    patterns = patterns or PATTERNS
    return next(
        (
            each for each in frames
            if each[4] and not any(pattern in each[1] for pattern in patterns)
        ),
        None,
    )
