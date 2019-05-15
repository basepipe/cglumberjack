import os
import shutil
import pandas as pd
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


class LJFileBrowser(QtWidgets.QTreeView):
    dropped_files = QtCore.Signal(object)
    selected = QtCore.Signal(object)
    initialized = QtCore.Signal()

    def __init__(self, parent=None, directory=None):
        QtWidgets.QTreeView.__init__(self, parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # self.clicked.connect(self.object_selected)
        self.directory = directory
        self.model = None
        self.selected_items = []
        if self.directory:
            self.populate(self.directory)
        else:
            return

    def populate(self, directory):
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.header().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.customContextMenuRequested.connect(self.right_click_menu)
        self.model = LJFileSystemModel(directory)
        self.directory = directory
        self.model.setRootPath((QtCore.QDir.rootPath()))
        self.setModel(self.model)
        self.setRootIndex(self.model.index(directory))
        self.setSortingEnabled(True)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.initialized.emit()

    def mouseReleaseEvent(self, e):
        super(LJFileBrowser, self).mouseReleaseEvent(e)
        self.object_selected()

    def right_click_menu(self):
        menu = QtGui.QMenu()
        view_in_explorer = menu.addAction('Show in Explorer')
        view_in_explorer.triggered.connect(self.view_in_explorer)

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def view_in_explorer(self):
        index = self.currentIndex()
        file_path = self.model.filePath(index)
        print 'viewing %s' % file_path

    def object_selected(self):
        files = []
        for index in self.selectedIndexes():
            file_path = self.model.filePath(index)
            if file_path not in files:
                files.append(file_path)
        self.selected_items = files
        self.selected.emit(files)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        index = self.currentIndex()
        to_path = self.model.filePath(index)
        if not to_path:
            to_path = self.directory
        if not os.path.isdir(to_path):
            to_path, filename = os.path.split(to_path)
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
                dir_, file_ = os.path.split(str(url.toLocalFile()))
                to_file = os.path.join(to_path, file_)
                print 'Copying %s to %s' % (str(url.toLocalFile()), to_file)
                shutil.copy2(str(url.toLocalFile()), to_file)
        else:
            print 'invalid'
            e.ignore()


class LJFileSystemModel(QtWidgets.QFileSystemModel):
    def __init__(self, dir):
        QtWidgets.QFileSystemModel.__init__(self)
        self.dir = dir
        pandas_file = os.path.join(self.dir, 'publish_data.csv')
        self.df = None
        self.df_exists = False
        if os.path.exists(pandas_file):
            self.df = pd.read_csv(pandas_file, names=["Filepath", "Tags", "Keep Client Naming",
                                                      "Seq", "Shot", "Task", "Project Filepath", "Status"])
            self.df_exists = True

    def columnCount(self, parent = QtCore.QModelIndex()):
        return super(LJFileSystemModel, self).columnCount()+2

    def data(self, i, role):
        if i.column() == self.columnCount()-2:
            if role == QtCore.Qt.DisplayRole:
                try:
                    row = self.df.loc[self.df['Filepath'] == self.filePath(i).replace('/', '\\')].index[0]
                    return self.df.loc[row, 'Status']
                except IndexError:
                    pass
            if role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignHCenter
        if i.column() == self.columnCount()-1:
            if role == QtCore.Qt.DisplayRole:
                try:
                    row = self.df.loc[self.df['Filepath'] == self.filePath(i).replace('/', '\\')].index[0]
                    return self.df.loc[row, 'Project Filepath']
                except IndexError:
                    pass


        return super(LJFileSystemModel, self).data(i, role)

