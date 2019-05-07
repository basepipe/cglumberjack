import logging
import sys
import multiprocessing

from cglcore.config import app_config


def _logging_setup():
    log_cfg = app_config()["logging"]
    level = log_cfg['level']
    fmt = log_cfg['format']
    if level in log_cfg:
        fmt = log_cfg[level]["format"]

    log_levels = {"debug": logging.DEBUG,
                  "critical": logging.CRITICAL,
                  "error": logging.ERROR,
                  "info": logging.INFO,
                  "warning": logging.WARNING
                  }
    logging.basicConfig(format=fmt, level=log_levels[level])
    logging.info("logging configured level %s ", level)


def do_app_init():
    """

    Run at start up of application to initialise necessary functions

    """
    if getattr(sys, 'frozen', False):
        multiprocessing.freeze_support()
    _logging_setup()
