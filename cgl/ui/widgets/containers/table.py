from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.util import UISettings, widget_name
from cgl.ui.widgets.base import StateSavers
from cgl.ui.util import drop_handler
from cgl.ui.widgets.containers.proxy import LJTableSearchProxy
from cgl.ui.widgets.containers.menu import LJMenu
from cgl.core.config import app_config

PROJ_MANAGEMENT = app_config()['account_info']['project_management']


class LJTableWidget(QtWidgets.QTableView):
    selected = QtCore.Signal(object)
    right_clicked = QtCore.Signal(object)
    dropped = QtCore.Signal(object)
    double_clicked = QtCore.Signal(object)

    def __init__(self, parent, path_object=None):
        QtWidgets.QTableView.__init__(self, parent)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.path_object = path_object
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.horizontalHeader().setMovable(True)
        self.menu = None
        self.search_wgt = None
        self.alphabet_header = None
        self.header_right_click_menu = LJMenu(self)
        # self.item_right_click_menu = LJMenu(self)
        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        StateSavers.remember_me(self)
        self.items_ = []
        # self.clicked.connect(self.row_selected)
        # self.activated.connect(self.row_selected)
        self.height_hint = 0
        self.width_hint = 0
        self.doubleClicked.connect(self.send_double_click_signal)

    def send_double_click_signal(self):
        items = []
        if self.selectionModel():
            for each in self.selectionModel().selectedRows():
                mdl_index = self.model().mapToSource(each)
                mdl = self.model().sourceModel()
                row = mdl_index.row()
                sel = mdl.data_[row]
                items.append(sel)
        else:
            print('No data to select')
        self.items_ = items
        try:
            self.double_clicked.emit(items)
        except IndexError:
            print('nothing selected')
            self.nothing_selected.emit()

    def row_count(self):
        return self.model().rowCount()

    def mouseReleaseEvent(self, e):
        super(LJTableWidget, self).mouseReleaseEvent(e)
        if e.button() == QtCore.Qt.LeftButton:
            self.viewClicked()

    def mousePressEvent(self, e):
        super(LJTableWidget, self).mousePressEvent(e)
        if e.button() == QtCore.Qt.RightButton:
            self.viewClicked()

    # noinspection PyShadowingNames,PyPep8
    def set_item_model(self, mdl, proxy=None):
        if not proxy:
            proxy = LJTableSearchProxy()
        self.setModel(proxy)
        # if isinstance(mdl, )
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
            self.header_right_click_menu.create_action(header_name,
                                                       lambda header_name=header_name: self.header_right_click_menu_trigger(header_name),
                                                       checkable=True)
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

    def viewClicked(self):
        items = []
        if self.selectionModel():
            for each in self.selectionModel().selectedRows():
                mdl_index = self.model().mapToSource(each)
                mdl = self.model().sourceModel()
                row = mdl_index.row()
                sel = mdl.data_[row]
                items.append(sel)
        else:
            print('No data to select')
        self.items_ = items
        try:
            self.selected.emit(items)
        except IndexError:
            print('nothing selected')
            self.nothing_selected.emit()

    def contextMenuEvent(self, event):
        self.menu = LJMenu(self)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.menu.create_action('Show in %s' % PROJ_MANAGEMENT, self.show_in_proj)
        self.menu.create_action('Share Project', self.share_project)
        self.menu.create_action('Calculate Project Size', self.calculate_project_size)
        self.menu.popup(QtGui.QCursor.pos())

    def calculate_project_size(self):
        from cgl.core.cgl_info import create_full_project_cgl_info
        mdl_index = self.model().mapToSource(self.selectionModel().selectedRows()[0])
        mdl = self.model().sourceModel()
        row = mdl_index.row()
        project = mdl.data_[row][0]
        company = self.path_object.company
        create_full_project_cgl_info(company=company, project=project)

    def share_project(self):
        from cgl.core.path import PathObject
        from cgl.plugins.syncthing.utils import share_project
        mdl_index = self.model().mapToSource(self.selectionModel().selectedRows()[0])
        mdl = self.model().sourceModel()
        row = mdl_index.row()
        project = mdl.data_[row]
        path_object = self.path_object.copy()
        path_object.set_attr(project=project[0])
        share_project(path_object)

    def show_in_proj(self):
        from cgl.core.path import PathObject, show_in_project_management
        mdl_index = self.model().mapToSource(self.selectionModel().selectedRows()[0])
        mdl = self.model().sourceModel()
        row = mdl_index.row()
        sel = mdl.data_[row]
        print(sel)
        path_object = self.path_object.copy(project=sel[0])
        print(path_object.path_root)
        show_in_project_management(path_object)

    def select_row_by_text(self, text, column=0):
        # search all the items in the table view and select the one that has 'text' in it.
        # .setSelection() is a massive part of figuring this out.
        data = []
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
        drop_handler(self.dropped, e)

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
                self.horizontalHeader().setResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)
                width = header.sectionSize(column)
                header.setResizeMode(column, QtWidgets.QHeaderView.Interactive)
                header.resizeSection(column, width)
                total_width += width
            except AttributeError:
                print('PySide2 compatibility issue: setResizeMode')
        for row in range(v_header.count()):
            try:
                self.verticalHeader().setResizeMode(row, QtWidgets.QHeaderView.ResizeToContents)
                height = v_header.sectionSize(row)
                v_header.setResizeMode(row, QtWidgets.QHeaderView.Interactive)
                v_header.resizeSection(row, height)
                total_height += height
            except AttributeError:
                print('PySide2 compatibility issue: setResizeMode')
        self.height_hint = total_height
        self.width_hint = total_width
        self.sizeHint()

    def sizeHint(self):
        return QtCore.QSize(self.height_hint, self.width_hint)

    def clear(self):
        self.clear()
        print('I should be clearing this')


class LJKeyPairTableWidget(LJTableWidget):
    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)

    def restore(self):
        pass
