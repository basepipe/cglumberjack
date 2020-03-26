import logging
from cgl.plugins.Qt import QtGui, QtCore
from core.utils.general import app_name


class UISettings(object):
    SETTINGS = None

    def __init__(self):
        if UISettings.SETTINGS is None:
            QtCore.QCoreApplication.setOrganizationName("cglumberjack")
            QtCore.QCoreApplication.setOrganizationDomain("cglumberjack.com")
            QtCore.QCoreApplication.setApplicationName(app_name())
            UISettings.SETTINGS = QtCore.QSettings()
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


def drop_handler(emitter, event):
    if event.mimeData().hasUrls:
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()
        file_list = []
        for url in event.mimeData().urls():
            file_list.append(str(url.toLocalFile()))
        emitter.emit(file_list)
    else:
        print 'invalid'
        event.ignore()


def define_palettes(color_a=QtGui.QColor(255, 0, 0), color_b=QtGui.QColor(0, 255, 0),
                    color_c=QtGui.QColor(0, 0, 0)):
    """
    by default gives you red, green, black palettes to work with.
    :return:
    """
    palette_a = QtGui.QPalette()
    palette_b = QtGui.QPalette()
    palette_c = QtGui.QPalette()
    palette_a.setColor(QtGui.QPalette.Foreground, color_a)
    palette_b.setColor(QtGui.QPalette.Foreground, color_b)
    palette_c.setColor(QtGui.QPalette.Foreground, color_c)
    return palette_a, palette_b, palette_c
