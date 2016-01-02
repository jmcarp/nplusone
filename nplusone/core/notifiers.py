# -*- coding: utf-8 -*-

import logging

from nplusone.core import exceptions


class Notifier(object):

    CONFIG_KEY = None
    ENABLED_DEFAULT = False

    @classmethod
    def is_enabled(cls, config):
        return (
            config.get(cls.CONFIG_KEY) or
            (
                cls.CONFIG_KEY not in config and
                cls.ENABLED_DEFAULT
            )
        )

    def __init__(self, config):
        self.config = config  # pragma: no cover

    def notify(self, model, field):
        pass  # pragma: no cover


class LogNotifier(Notifier):

    CONFIG_KEY = 'NPLUSONE_LOG'
    ENABLED_DEFAULT = True

    def __init__(self, config):
        self.logger = config.get('NPLUSONE_LOGGER', logging.getLogger('nplusone'))
        self.level = config.get('NPLUSONE_LOG_LEVEL', logging.DEBUG)

    def notify(self, message):
        self.logger.log(self.level, message.message)


class ErrorNotifier(Notifier):

    CONFIG_KEY = 'NPLUSONE_RAISE'
    ENABLED_DEFAULT = False

    def __init__(self, config):
        self.error = config.get('NPLUSONE_ERROR', exceptions.NPlusOneError)

    def notify(self, message):
        raise self.error(message.message)


def init(config):
    return [
        notifier(config) for notifier in (LogNotifier, ErrorNotifier)
        if notifier.is_enabled(config)
    ]
