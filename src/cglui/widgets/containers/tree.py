from Qt import QtCore, QtWidgets, QtGui
from cglui.util import UISettings
from cglui.widgets.base import StateSavers
from cglui.widgets.combo import AdvComboBox
from cglcore.path import get_file_icon

FILEPATH = 0
FILENAME = 1
FILETYPE = 2
FRANGE = 3
TAGS = 4
KEEP_CLIENT_NAMING = 5
SCOPE = 6
SEQ = 7
SHOT = 8
TASK = 9
PUBLISH_FILEPATH = 10
PUBLISH_DATE = 11
STATUS = 12


class ProductionComboDelegate(QtWidgets.QItemDelegate):
    index_changed = QtCore.Signal(object)

    def __init__(self, parent, items):
        QtWidgets.QItemDelegate.__init__(self, parent)
        self.items = items

    def createEditor(self, parent):
        combo = AdvComboBox(parent)
        combo.addItems(self.items)
        combo.setEnabled(True)
        if not self.items:
            combo.setEnabled(False)
        combo.currentIndexChanged.connect(self.send_index_change)
        return combo

    @staticmethod
    def setEditorData(editor, index):
        print editor, index

    def send_index_change(self):
        print self.__dict__
        self.index_changed.emit(self.sender().currentText())

    @staticmethod
    def reload_items(items):
        print items


class LJTreeWidget(QtWidgets.QTreeView):
    nothing_selected = QtCore.Signal()
    selected = QtCore.Signal(object)
    dropped = QtCore.Signal(object)
    header_labels = []

    def __init__(self, parent=None, parents=None):
        QtWidgets.QTreeView.__init__(self, parent)
        StateSavers.remember_me(self)

        self.items_ = []
        self.model = QtGui.QStandardItemModel()
        self.setUniformRowHeights(True)
        # connect items
        if parents:
            self.populate_tree(parents)
        self.clicked.connect(self.row_selected)
        self.activated.connect(self.row_selected)
        self.horizontalScrollBar().setEnabled(False)
        self.height_hint = 150
        self.width_hint = 0
        self.path_object = None

    def populate_from_data_frame(self, path_object, data_frame, header):
        self.height_hint = 150
        self.path_object = path_object
        for row in data_frame.itertuples():
            filename_item = QtWidgets.QStandardItem(row.Filename)
            filename_item.setIcon(QtGui.QIcon(get_file_icon(row.Filename)))
            self.model.appendRow([QtWidgets.QStandardItem(row.Filepath),
                                  filename_item,
                                  QtWidgets.QStandardItem(row.Filetype),
                                  QtWidgets.QStandardItem(row.Frame_Range),
                                  QtWidgets.QStandardItem(row.Tags),
                                  QtWidgets.QStandardItem(row.Keep_Client_Naming),
                                  QtWidgets.QStandardItem(row.Scope),
                                  QtWidgets.QStandardItem(row.Seq),
                                  QtWidgets.QStandardItem(row.Shot),
                                  QtWidgets.QStandardItem(row.Task),
                                  QtWidgets.QStandardItem(row.Publish_Filepath),
                                  QtWidgets.QStandardItem(row.Publish_Date),
                                  QtWidgets.QStandardItem(row.Status)])
        self.model.setHorizontalHeaderLabels(header)
        self.header().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.header().setMinimumSectionSize(140)
        # scopes_del = ProductionComboDelegate(self, scopes)
        # scopes_del.index_changed.connect(self.scope_changed)
        # self.setItemDelegateForColumn(SCOPE, scopes_del)
        self.hideColumn(FILEPATH)
        self.hideColumn(FILETYPE)
        self.hideColumn(KEEP_CLIENT_NAMING)
        self.hideColumn(SEQ)
        self.hideColumn(SHOT)
        self.hideColumn(SCOPE)
        self.hideColumn(TASK)
        self.hideColumn(TAGS)
        self.hideColumn(PUBLISH_FILEPATH)

        # resize the tree view to the actual stuff.
        self.setMinimumWidth(self.width_hint)
        self.setMinimumHeight(self.height_hint)

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
        row = []
        if self.selectionModel():
            for r in self.selectionModel().selectedRows():
                for column in range(self.column_count()):
                    print column, self.model.item(r.row(), column).text()
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
        data = []
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

    @staticmethod
    def on_closing():
        settings = UISettings.settings()
        print settings, 'Need to adjust this code'
        # hheading = self.horizontalHeader()
        # settings.setValue(widget_name(self) + ":hheading", hheading.saveState())

    def resizeEvent(self, event):
        # TODO - this doesn't work on mac, but does on windows
        """ Resize all sections to content and user interactive """
        super(LJTreeWidget, self).resizeEvent(event)
        header = self.header()
        total_width = 0
        for column in range(header.count()):
            try:
                header.setResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)
                width = header.sectionSize(column)
                header.setResizeMode(column, QtWidgets.QHeaderView.Interactive)
                header.resizeSection(column, width)
                total_width += width
            except AttributeError:
                print 'PySide2 compatibility issue: setResizeMode'
        for row in range(self.row_count()):
            self.height_hint += 24
        self.width_hint = total_width
        self.sizeHint()

    def sizeHint(self):
        return QtCore.QSize(self.height_hint, self.width_hint)


