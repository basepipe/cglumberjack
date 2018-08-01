import logging

from Qt.QtCore import QSettings, QCoreApplication
from cglcore.util import app_name


class UISettings(object):
    SETTINGS = None

    def __init__(self):
        if UISettings.SETTINGS is None:
            QCoreApplication.setOrganizationName("cglumberjack")
            QCoreApplication.setOrganizationDomain("cgjumberjack.com")
            QCoreApplication.setApplicationName(app_name())
            UISettings.SETTINGS = QSettings()
            logging.info("using settings file %s", UISettings.SETTINGS.fileName())

    @classmethod
    def settings(cls):
        return cls().SETTINGS


def widget_name(obj):
    """
    returns a standard widget name as used in settings
    Args:
        obj: object to find name for

    Returns: "%s:%s" % (obj.__class__.__name__, obj.getObjectName())

    """
    return "%s:%s" % (obj.__class__.__name__, obj.objectName())
