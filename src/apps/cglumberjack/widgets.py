import os
from Qt import QtCore, QtWidgets
from Qt.QtCore import Qt
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.menu import LJMenu
from cglcore.path import PathParser, add_to_system
from cglcore import path

class FileTableModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        if role == Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                icon_path = os.path.join(path.icon_path(), 'folder2.png')
                return QtWidgets.QIcon(icon_path)
        # if role == Qt.ToolTipRole:
        #     return "hello tom"


class AddAssetModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        if role == Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                icon_path = os.path.join(path.icon_path(), 'folder2.png')
                return QtWidgets.QIcon(icon_path)
        # if role == Qt.ToolTipRole:
        #     return "hello tom"


class FileTable(LJTableWidget):
    files_added = QtCore.Signal(basestring)
    file_selected = QtCore.Signal(object)

    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)
        self.setShowGrid(False)
        self.setAcceptDrops(True)

    def mouseReleaseEvent(self, e):
        super(FileTable, self).mouseReleaseEvent(e)
        self.row_selected()

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
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
            self.files_added.emit(file_list)
        else:
            print 'invalid'
            e.ignore()


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.button = QtWidgets.QToolButton()
        self.button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.setMinimumHeight(200)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addWidget(self.data_table, 1)

        self.message.hide()
        self.button.clicked.connect(self.on_button_clicked)

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_button_clicked(self):
        data = {'title': self.label}
        self.button_clicked.emit(data)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())
