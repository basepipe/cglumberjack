from Qt import QtCore, QtWidgets, QtGui
from cglui.util import UISettings
from cglui.widgets.base import StateSavers
from cglui.widgets.combo import AdvComboBox
from cglcore.path import get_file_icon

FILEPATH = 1
FILENAME = 0
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
PARENT = 13


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


class LJTreeModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self)


class LJTreeWidget(QtWidgets.QTreeView):
    nothing_selected = QtCore.Signal()
    selected = QtCore.Signal(object)
    files_added = QtCore.Signal(object)
    header_labels = []

    def __init__(self, parent=None, parents=None):
        QtWidgets.QTreeView.__init__(self, parent)
        StateSavers.remember_me(self)

        self.items_ = []

        self.model = LJTreeModel()
        self.setModel(self.model)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setUniformRowHeights(True)
        # connect items
        if parents:
            self.populate_tree(parents)
        self.clicked.connect(self.row_selected)
        self.activated.connect(self.row_selected)
        self.horizontalScrollBar().setEnabled(False)
        self.height_hint = 200
        self.width_hint = 400
        self.path_object = None
        self.setMinimumHeight(200)
        self.setMaximumHeight(200)

    def populate_from_data_frame(self, path_object, data_frame, header):
        self.height_hint = 150
        self.path_object = path_object
        for row in data_frame.itertuples():
            filename_item = QtWidgets.QStandardItem(row.Filename)
            filename_item.setIcon(QtGui.QIcon(get_file_icon(row.Filename)))
            if 'Parent' in data_frame:
                row_list = [filename_item,
                            QtWidgets.QStandardItem(row.Filepath),
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
                            QtWidgets.QStandardItem(row.Status),
                            QtWidgets.QStandardItem(row.Parent)]
                if row.Parent == 'self':
                    self.model.appendRow(row_list)
                else:
                    # parent = find the row where filename matches 'parent'
                    items = self.model.findItems(str(row.Parent), column=FILENAME)
                    parent = items[-1]
                    parent.appendRow(row_list)
        self.model.setHorizontalHeaderLabels(header)
        self.header().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.header().setMinimumSectionSize(140)
        # scopes_del = ProductionComboDelegate(self, scopes)
        # scopes_del.index_changed.connect(self.scope_changed)
        # self.setItemDelegateForColumn(SCOPE, scopes_del)
        self.hideColumn(FILEPATH)
        self.hideColumn(FILETYPE)
        self.hideColumn(KEEP_CLIENT_NAMING)
        # self.hideColumn(SEQ)
        # self.hideColumn(SHOT)
        self.hideColumn(SCOPE)
        self.hideColumn(TASK)
        self.hideColumn(TAGS)
        # self.hideColumn(PUBLISH_FILEPATH)
        self.hideColumn(PARENT)

        # resize the tree view to the actual stuff.
        self.setMinimumWidth(self.width_hint)
        # self.setMinimumHeight(400)

    def set_header_labels(self, mdl, headers):
        self.header_labels = headers
        mdl.setHorizontalHeaderLabels(headers)

    def row_count(self):
        print 'row count:', self.model.rowCount()
        return self.model.rowCount()

    def column_count(self):
        return self.model.columnCount()

    def set_text(self, row, column_number, new_text):
        parent = None
        if row.parent().row() != -1:
            parent = row.parent()
        if parent:
            self.model.itemFromIndex(parent.child(row.row(), column_number)).setText(new_text)
        else:
            self.model.item(row.row(), column_number).setText(new_text)
        pass

    def row_selected(self):
        items = []
        row = []
        parent = None
        if self.selectionModel():
            for r in self.selectionModel().selectedRows():
                if r.parent().row() != -1:
                    parent = r.parent()
                for column in range(self.column_count()):
                    # print column, self.model.item(r.row(), column).text()
                    if parent:
                        item = parent.child(r.row(), column).data(QtCore.Qt.DisplayRole)
                    else:
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
        self.model = LJTreeModel()
        self.setModel(self.model)
        self.setAcceptDrops(True)

    @staticmethod
    def on_closing():
        settings = UISettings.settings()
        print settings, 'Need to adjust this code'
        # hheading = self.horizontalHeader()
        # settings.setValue(widget_name(self) + ":hheading", hheading.saveState())

    # def resizeEvent(self, event):
    #     # TODO - this doesn't work on mac, but does on windows
    #     """ Resize all sections to content and user interactive """
    #     super(LJTreeWidget, self).resizeEvent(event)
    #     header = self.header()
    #     total_width = 0
    #     for column in range(header.count()):
    #         try:
    #             header.setResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)
    #             width = header.sectionSize(column)
    #             header.setResizeMode(column, QtWidgets.QHeaderView.Interactive)
    #             header.resizeSection(column, width)
    #             total_width += width
    #         except AttributeError:
    #             print 'PySide2 compatibility issue: setResizeMode'
    #     for row in range(self.row_count()):
    #         self.height_hint += 24
    #     self.width_hint = total_width
    #     self.sizeHint()
    #
    # def sizeHint(self):
    #     return QtCore.QSize(self.height_hint, self.width_hint)

    def dropEvent(self, event):
        print 'dropping like its hot'
        print self.height_hint
        print event.mimeData()
        # if e.mimeData().hasUrls:
        #     e.setDropAction(QtCore.Qt.CopyAction)
        #     e.accept()
        #     file_list = []
        #     for url in e.mimeData().urls():
        #         file_list.append(str(url.toLocalFile()))
        #     self.files_added.emit(file_list)
        # else:
        #     e.ignore()


