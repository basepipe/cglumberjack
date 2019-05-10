from Qt import QtCore, QtGui, QtWidgets


class LJFileBrowser(QtWidgets.QTreeView):
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

