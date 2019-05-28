from Qt import QtCore, QtWidgets, QtGui
from cglui.util import UISettings, widget_name
from cglui.widgets.base import StateSavers
from cglcore.path import get_file_icon, get_file_type
from cglui.widgets.containers.menu import LJMenu
from cglui.widgets.containers.proxy import LJTableSearchProxy


class LJTreeWidget(QtWidgets.QTreeView):
    selected = QtCore.Signal(object)
    dropped = QtCore.Signal(object)

    def __init__(self, parent, header_list=[], parents=[]):
        QtWidgets.QTreeView.__init__(self, parent)
        StateSavers.remember_me(self)
        self.items_ = []
        self.model = QtGui.QStandardItemModel()
        self.header_labels = header_list
        self.set_header_labels(self.model, headers=self.header_labels)
        self.setUniformRowHeights(True)
        # connect items
        if parents:
            self.populate_tree(parents)
        self.clicked.connect(self.row_selected)
        self.activated.connect(self.row_selected)

    def populate_parents(self, list):
        # go through the first
        for p in list:
            parent1 = QtWidgets.QStandardItem(p)
            type_ = get_file_type(p)
            parent1.setIcon(QtGui.QIcon(get_file_icon(p)))
            file_type = QtWidgets.QStandardItem(type_)
            self.model.appendRow([parent1, file_type])

    def set_header_labels(self, mdl, headers):
        self.header_labels = headers
        print 'setting ', headers
        mdl.setHorizontalHeaderLabels(headers)

    def row_count(self):
        return self.model.rowCount()

    def column_count(self):
        return self.model.columnCount()

    def row_selected(self):
        items = []
        if self.selectionModel():
            print 'column count', self.column_count()
            for r in self.selectionModel().selectedRows():
                row = []
                for column in range(self.column_count()):
                    item = self.model.item(r.row(), column).text()
                    row.append(item)
            items.append(row)
        else:
            print 'No data to select'
        self.items_ = items
        try:
            self.selected.emit(items)
        except IndexError:
            print 'nothing selected'
            self.nothing_selected.emit()

    def select_row_by_text(self, text, column=0):
        # search all the items in the table view and select the one that has 'text' in it.
        # .setSelection() is a massive part of figuring this out.
        row_count = self.model().rowCount()
        for row in range(0, row_count + 1):
            src_index = self.model().index(row, column)
            data = self.model().data(src_index, QtCore.Qt.DisplayRole)
            if data == text:
                self.selectRow(row)
        self.selected.emit([data])

    def clear(self):
        """
        :return:
        """
        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)

    def on_closing(self):
        settings = UISettings.settings()
        hheading = self.horizontalHeader()
        settings.setValue(widget_name(self) + ":hheading", hheading.saveState())


