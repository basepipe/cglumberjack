from Qt import QtCore

from Qt.QtWidgets import QTableView, QHeaderView

from cglui.util import UISettings, widget_name
from cglui.widgets.base import StateSavers
from cglui.widgets.containers.proxy import LJTableSearchProxy
from cglui.widgets.containers.menu import LJMenu


class LJTableWidget(QTableView):
    selected = QtCore.Signal(object)
    dropped = QtCore.Signal(object)

    def __init__(self, parent):
        QTableView.__init__(self, parent)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        #self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.horizontalHeader().setMovable(True)
        self.search_wgt = None
        self.alphabet_header = None
        self.header_right_click_menu = LJMenu(self)
        # self.item_right_click_menu = LJMenu(self)
        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        StateSavers.remember_me(self)
        self.items_ = []
        self.clicked.connect(self.row_selected)
        self.activated.connect(self.row_selected)
        self.height_hint = 0
        self.width_hint = 0
        # self.setProperty('class', 'basic')

    def row_count(self):
        return self.model().rowCount()

    def mouseReleaseEvent(self, e):
        super(LJTableWidget, self).mouseReleaseEvent(e)
        self.row_selected()

    def set_item_model(self, mdl, proxy=None):
        if proxy is None:
            proxy = LJTableSearchProxy()
        self.setModel(proxy)
        proxy.setSourceModel(mdl)
        self.setSortingEnabled(True)

        self.horizontalHeader().customContextMenuRequested.connect(self.header_right_click)
        self.alphabet_header = sorted(mdl.headers)
        settings = UISettings.settings()
        hheading = self.horizontalHeader()
        state = settings.value(widget_name(self) + ":hheading", None)
        if state:
            hheading.restoreState(state)

        for header_name in self.alphabet_header:
            self.header_right_click_menu.create_action(
                header_name, lambda header_name=header_name: self.header_right_click_menu_trigger(header_name), checkable=True)
            if not self.isColumnHidden(mdl.headers.index(header_name)):
                 self.header_right_click_menu.actions()[self.alphabet_header.index(header_name)].setChecked(True)

    def set_search_box(self, wgt):
        self.search_wgt = wgt
        self.model().set_search_widget(wgt)
        wgt.textChanged.connect(self.model().invalidateFilter)

    # Right Click Menu Function
    def header_right_click(self, position):
        self.header_right_click_menu.exec_(self.mapToGlobal(position))

    def header_right_click_menu_trigger(self, header):
        mdl = self.model()
        if isinstance(mdl, QtCore.QSortFilterProxyModel):
            mdl = mdl.sourceModel()

        if self.isColumnHidden(mdl.headers.index(header)):
            self.setColumnHidden(mdl.headers.index(header), False)
        else:
            flag = False
            for i in range(len(mdl.headers)):
                if i == mdl.headers.index(header):
                    continue
                elif not self.isColumnHidden(i):
                    flag = True
                    break
            if flag:
                self.setColumnHidden(mdl.headers.index(header), True)
            else:
                self.header_right_click_menu.actions()[self.alphabet_header.index(header)].setChecked(True)

    def row_selected(self):
        items = []
        if self.selectionModel():
            for each in self.selectionModel().selectedRows():
                mdl_index = self.model().mapToSource(each)
                mdl = self.model().sourceModel()
                row = mdl_index.row()
                sel = mdl.data_[row]
                items.append(sel)
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

    def on_closing(self):
        settings = UISettings.settings()
        hheading = self.horizontalHeader()
        settings.setValue(widget_name(self) + ":hheading", hheading.saveState())

    def set_draggable(self, value):
        self.setAcceptDrops(value)

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
        # this is set up specifically to handle files as that's the only use case
        # we've encountered to date, i'm sure we can put options in as they arise.
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
            self.dropped.emit(file_list)
        else:
            print 'invalid'
            e.ignore()

    def resizeEvent(self, event):
        # TODO - this doesn't work on mac, but does on windows
        """ Resize all sections to content and user interactive """
        super(LJTableWidget, self).resizeEvent(event)
        header = self.horizontalHeader()
        v_header = self.verticalHeader()
        total_height = 0
        total_width = 0
        for column in range(header.count()):
            try:
                self.horizontalHeader().setResizeMode(column, QHeaderView.ResizeToContents)
                width = header.sectionSize(column)
                header.setResizeMode(column, QHeaderView.Interactive)
                header.resizeSection(column, width)
                total_width += width
            except AttributeError:
                print 'PySide2 compatibilty issue: setResizeMode'
        for row in range(v_header.count()):
            try:
                self.verticalHeader().setResizeMode(row, QHeaderView.ResizeToContents)
                height = v_header.sectionSize(row)
                v_header.setResizeMode(row, QHeaderView.Interactive)
                v_header.resizeSection(row, height)
                total_height += height
            except AttributeError:
                print 'PySide2 compatibilty issue: setResizeMode'
        self.height_hint = total_height
        self.width_hint = total_width
        self.sizeHint()

    def sizeHint(self):
        return QtCore.QSize(self.height_hint, self.width_hint)


class LJKeyPairTableWidget(LJTableWidget):
    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)

    def restore(self):
        pass
