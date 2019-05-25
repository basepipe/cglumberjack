import os
import shutil
import pandas as pd
from Qt import QtCore, QtGui, QtWidgets
from cglcore.path import start


class LJFileBrowser2(QtWidgets.QTreeView):
    def __init__(self, parent=None, directory=None):
        QtWidgets.QTreeView.__init__(self, parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        if directory:
            self.populate()

    def populate(self, directory):
        path = directory
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath((QtCore.QDir.rootPath()))
        self.setModel(self.model)
        self.setRootIndex(self.model.index(path))
        self.setSortingEnabled(True)


class LJFileBrowser(QtWidgets.QTreeView):
    # dropped_files = QtCore.Signal(object)
    selected = QtCore.Signal(object)
    initialized = QtCore.Signal()

    def __init__(self, parent=None, directory=None):
        QtWidgets.QTreeView.__init__(self, parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # self.clicked.connect(self.object_selected)
        self.directory = directory
        self.model = None
        self.filter = ["*.csv"]
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
        # TODO - this filters everything BUT my filter, i want to filter ONLY what i've listed.
        # self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)
        # self.model.setNameFilters(self.filter)
        # self.model.setNameFilterDisables(0)
        self.directory = directory
        self.model.setRootPath((QtCore.QDir.rootPath()))
        self.setModel(self.model)
        self.setRootIndex(self.model.index(directory))
        self.setSortingEnabled(True)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        # self.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
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
        start(os.path.dirname(file_path))
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
    def __init__(self, dir_):
        QtWidgets.QFileSystemModel.__init__(self)
        self.dir = dir_
        pandas_file = os.path.join(self.dir, 'publish_data.csv')
        self.df = None
        self.df_exists = False
        if os.path.exists(pandas_file):
            self.df = pd.read_csv(pandas_file, names=["Filepath", "Tags", "Keep Client Naming", "Scope",
                                                      "Seq", "Shot", "Task", "Project Filepath", "Status"])
            self.df_exists = True

    def columnCount(self, parent=QtCore.QModelIndex()):
        return super(LJFileSystemModel, self).columnCount()+1

    def data(self, i, role):
        if i.column() == self.columnCount()-1:
            if role == QtCore.Qt.DisplayRole:
                try:
                    if self.df_exists:
                        row = self.df.loc[self.df['Filepath'] == self.filePath(i).replace('/', '\\')].index[0]
                        return self.df.loc[row, 'Status']
                    else:
                        return 'Imported'
                except IndexError:
                    pass
            if role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignHCenter
        #if i.column() == self.columnCount()-1:
        #    if role == QtCore.Qt.DisplayRole:
        #        try:
        #            if self.df_exists:
        #                row = self.df.loc[self.df['Filepath'] == self.filePath(i).replace('/', '\\')].index[0]
        #                return self.df.loc[row, 'Project Filepath']
        #            else:
        #                return 'Click To Tag'
        #        except IndexError:
        #            pass
        return super(LJFileSystemModel, self).data(i, role)
