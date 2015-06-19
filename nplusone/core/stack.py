# -*- coding: utf-8 -*-

import inspect


def get_caller():
    frames = inspect.stack()
    patterns = ['site-packages', 'py.test']
    return next(
        (
            each for each in reversed(frames)
            if each[4] and not any(pattern in each[1] for pattern in patterns)
        ),
        None,
    )
