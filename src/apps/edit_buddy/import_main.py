import platform
import os
import psutil
import datetime
import pandas as pd
import glob
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJDialog
from cglui.widgets.base import LJFileBrowser
from cglui.widgets.dialog import InputDialog
from cglui.widgets.project_selection_module import LJListWidget, LabelComboRow
from cglcore.config import app_config
from cglcore.path import PathObject, CreateProductionData


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])


class ImportBrowser(LJDialog):

    def __init__(self, parent=None):
        super(ImportBrowser, self).__init__()
        h_layout = QtWidgets.QVBoxLayout(self)
        v_layout = QtWidgets.QHBoxLayout()

        self.root = None
        self.company = None
        self.project = None
        self.data_frame = None
        self.path_object = PathObject(r'D:\cgl-fsutests\source\test5\IO')
        self.path_object.set_attr(scope='IO')
        self.path_object.set_attr(input_company='*')

        self.file_tree = LJFileBrowser(self)

        self.company_widget = LJListWidget('Company')
        self.import_events = LJListWidget('Import Versions')

        v_layout.addWidget(self.company_widget)
        v_layout.addWidget(self.import_events)
        h_layout.addLayout(v_layout)
        h_layout.addWidget(self.file_tree)

        self.load_companies()

        self.company_widget.list.clicked.connect(self.on_company_changed)
        self.import_events.list.clicked.connect(self.on_event_selected)

    def load_companies(self):
        self.company_widget.list.clear()
        dir_ = self.path_object.glob_project_element('input_company')
        if 'INTERNAL' not in dir_:
            dir_.insert(0, 'INTERNAL')
        self.company_widget.list.addItems(dir_)
        #self.on_company_changed()

    def on_company_changed(self):
        self.company_widget.list.selectedItems()[-1].text()
        self.path_object.set_attr(input_company=self.company_widget.list.selectedItems()[-1].text())
        self.load_import_events()

    def load_import_events(self):
        self.import_events.list.clear()
        events = glob.glob('%s/%s' % (self.path_object.split_after('input_company'), '*'))
        for e in events:
            self.import_events.list.addItem(os.path.split(e)[-1])

    def on_event_selected(self):
        print self.import_events.list.selectedItems()[-1].text()
        self.path_object.set_attr(version=self.import_events.list.selectedItems()[-1].text())
        # Load the Tree Widget
        self.populate_tree()

    def populate_tree(self):
        self.file_tree.populate(directory=self.path_object.path_root)


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = ImportBrowser()
    td.setWindowTitle('Ingest-o-matic')
    td.show()
    td.raise_()
    app.exec_()