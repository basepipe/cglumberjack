from Qt import QtWidgets, QtCore, QtGui
from cglui.util import UISettings, widget_name
from cglcore.util import app_name


class StateSavers(QtCore.QObject):
    SAVERS = None

    def __init__(self):
        if StateSavers.SAVERS is None:
            StateSavers.SAVERS = set()

    @classmethod
    def remember_me(cls, obj):
        cls().SAVERS.add(obj)

    @classmethod
    def notify_savers(cls):
        for x in cls().SAVERS:
            x.on_closing()


def _restore_size(self, default_size):
    if default_size is None:
        default_size = QtCore.QSize(800, 800)
    settings = UISettings.settings()
    geo = settings.value(widget_name(self))
    if geo:
        self.setGeometry(geo)
    else:
        self.resize(default_size)


class LJMainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_size=None):
        QtWidgets.QMainWindow.__init__(self)
        title = app_name(human=True)
        self.setWindowTitle(title.title())
        _restore_size(self, default_size)

    def closeEvent(self, event):
        geo = self.geometry()
        settings = UISettings.settings()
        settings.setValue(widget_name(self), geo)
        super(LJMainWindow, self).closeEvent(event)


class LJSplitter(QtWidgets.QSplitter):
    def __init__(self, parent):
        QtWidgets.QSplitter.__init__(self, parent)

    def restore(self):
        settings = UISettings.settings()
        state = settings.value(widget_name(self))
        if state:
            self.restoreState(state)
        self.splitterMoved.connect(self.record_state)

    def record_state(self, pos, index):
        settings = UISettings.settings()
        settings.setValue(widget_name(self), self.saveState())


class LJDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)


class LJWindow(QtWidgets.QWidget):
    def __init__(self, parent, default_size=None):
        QtWidgets.QWidget.__init__(self, parent)
        _restore_size(self, default_size)

    def closeEvent(self, event):
        wn = widget_name(self)
        if wn != "LJWindow:":
            geo = self.geometry()
            settings = UISettings.settings()
            settings.setValue(widget_name(self), geo)
            super(LJWindow, self).closeEvent(event)
        StateSavers.notify_savers()


class LJWidgetWrapper(LJDialog):

    def __init__(self, parent=None, title='', widget=None):
        LJDialog.__init__(self, parent=parent)
        widget.parent_ = self
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(widget)
        self.setWindowTitle(title)
        self.setLayout(self.layout)




