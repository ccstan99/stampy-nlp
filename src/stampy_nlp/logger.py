import logging
from stampy_nlp import settings


logging.basicConfig(level=settings.LOG_LEVEL)


def make_logger(name, level=None):
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger


def log_query(name, type_, query):
    logger = make_logger('queries')
    logger.info('%s %s: %s', type_, name, query)
