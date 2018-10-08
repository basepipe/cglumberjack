import platform
import os
import psutil
import datetime
import pandas as pd
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJDialog
from cglui.widgets.dialog import InputDialog
from cglui.widgets.project_selection_module import AssetWidget, LabelComboRow, LabelEditRow, ProjectControlCenter
from core.config import app_config
from core.path import PathObject, CreateProductionData


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
        self.destination_tree = QtWidgets.QTreeView()
        self.root = None
        self.company = None
        self.project = None
        header = self.destination_tree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.destination_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.model = QtGui.QStandardItemModel()
        self.model.setColumnCount(2)
        self.destination_tree.header().hide()
        self.destination_tree.setModel(self.model)

        self.h_layout = QtWidgets.QHBoxLayout()
        self.data_frame = {}
        self.left_column = QtWidgets.QVBoxLayout()
        self.media_internal = QtWidgets.QLabel('Internal Media')
        self.media_label = QtWidgets.QLabel('Connected Media')
        self.media_sources = QtWidgets.QListWidget()
        self.media_sources.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.media_sources.setEnabled(False)
        self.control_center = ProjectControlCenter()
        self.control_center.hide_filters()

        self.left_column.addWidget(self.media_label)
        self.left_column.addWidget(self.media_sources)

        self.right_column = QtWidgets.QVBoxLayout()
        self.ingest_button = QtWidgets.QPushButton()
        self.ingest_button.setText('Ingest')
        self.source_dict = {}

        self.capture_date = LabelEditRow("Capture Date")
        self.uncategorized_files = QtWidgets.QLabel("0 Uncategorized Files")
        # TODO - i want drop down menus for tasks for each of these file types so i know where they're all going.

        self.right_column.addWidget(self.control_center)
        self.right_column.addWidget(self.ingest_button)

        self.date_list = QtWidgets.QListWidget()
        self.file_list = QtWidgets.QListWidget()
        self.h_layout.addLayout(self.right_column)
        self.h_layout.addLayout(self.left_column)
        self.h_layout.addWidget(self.destination_tree)

        self.setLayout(self.h_layout)

        self.load_media()
        self.hide_middle_column()
        self.hide_right_column()
        self.file_data = {}
        self.media_sources.itemSelectionChanged.connect(self.on_media_selected)
        self.date_list.itemSelectionChanged.connect(self.on_date_selected)
        self.control_center.project_changed.connect(self.on_project_selected)
        #self.company_chooser.add_button.clicked.connect(self.on_create_company_clicked)
        #self.project_chooser.add_button.clicked.connect(self.on_create_project_clicked)

    def hide_middle_column(self):
        self.media_internal.hide()
        self.media_label.hide()
        self.media_sources.hide()

    def hide_right_column(self):
        self.destination_tree.hide()

    def show_right_column(self):
        self.destination_tree.show()
        
    def show_middle_column(self):
        # self.media_internal.show()
        self.media_label.show()
        self.media_sources.show()

    def on_create_company_clicked(self):
        # TODO This needs to be a universal method in some library
        dialog = InputDialog(title='Create Company', message='Type a Company Name', line_edit=True)
        dialog.exec_()
        if dialog.button == 'Ok':
            self.company = '%s' % dialog.line_edit.text()
            d = {'root': self.root,
                 'company': self.company}
            self.create_company_globals(dialog.line_edit.text())
            CreateProductionData(d)
            self.load_companies(company=self.company)
            self.load_projects()

    def on_create_project_clicked(self):
        print 'create project'

    def populate_tree(self):
        self.model.removeRows(0, self.model.rowCount())
        for date in sorted(self.data_frame.creation_date.unique()):
            # Add all the date to the tree widget
            date_object = QtGui.QStandardItem(str(date))
            date_object.setEditable(False)
            self.model.appendRow(date_object)
            for each in sorted(self.data_frame.file_category.unique()):
                fc_object = QtGui.QStandardItem(str(each))
                fc_object.setEditable(False)
                date_object.appendRow(fc_object)
                # return list of file names that match the date and the category
                df = self.data_frame[(self.data_frame['file_category'] == each) & (self.data_frame['creation_date'] == date)]
                for file_ in sorted(df.fullpath.tolist()):
                    dir_, file_ = os.path.split(file_)
                    d = {'root': self.control_center.root,
                         'company': self.control_center.company,
                         'context': 'source',
                         'project': self.project,
                         'scope': 'assets',
                         'seq': 'ingestion',
                         'shot': str(date),
                         'filename': file_}
                    path_object = PathObject(d)
                    file_object = QtGui.QStandardItem(str(file_))
                    file_object.setEditable(False)
                    fc_dest = QtGui.QStandardItem(path_object.path_root)
                    fc_dest.setEditable(False)
                    fc_object.appendRow([file_object, fc_dest])
                # TODO - need something for removing the file_category if there are no files in it.
                # TODO - if the destination file exists the node should be grey
                # TODO - if all the destination files in a task exist the task should be grey
                # TODO - if all the tasks are grey the date should be grey
                # TODO - if the task is empty the task should be grey

    def load_media(self):
        disks = []
        if platform.system() == "Windows":
            return psutil.disk_partitions()
        else:
            disks = psutil.disk_partitions()
            mounts = []
            for item in disks:
                if item.mountpoint != os.path.abspath(os.sep):
                    if 'private' not in item.mountpoint:
                        list_item = QtWidgets.QListWidgetItem(str(item.mountpoint))
                        self.media_sources.addItem(list_item)
                        mounts.append(item.mountpoint)
            return mounts

    def on_media_selected(self):
        self.date_list.clear()
        for each in self.media_sources.selectedItems():
            if each.text() in self.source_dict:
                self.data_frame = self.source_dict[each.text()]
            else:
            # need to adjust this for multiple sources
                self.data_frame = self.local_tree_dataframe(each.text())
                self.source_dict[each.text()] = self.data_frame
        self.date_list.addItems(sorted(self.data_frame.creation_date.unique()))
        self.populate_tree()
        self.show_right_column()

    def on_date_selected(self):
        self.file_list.clear()
        for each in self.date_list.selectedItems():
            df = self.data_frame[self.data_frame['creation_date'].isin([each.text()])]
            self.file_list.addItems(sorted(df.fullpath.tolist()))
        self.populate_tree()


    def on_project_selected(self, data):
        self.project = data
        self.media_sources.setEnabled(True)
        self.show_middle_column()


    @staticmethod
    def get_creation_date(path_to_file):
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        elif platform.system() == 'Darwin':
            stat = os.stat(path_to_file)
            return stat.st_birthtime

    def local_tree_dataframe(self, folder):
        """Converts a local tree on disk to a Pandas DataFrame
        In [1]: from syncs3 import local_tree_dataframe

        In [2]: pd = local_tree_dataframe("test-folder/")

        In [3]: print(pd)
        Out[3]:
             filename                                           fullpath
        0  level1.txt  /Users/noahgift/src/core_tools/test-folder/lev...
        1  level2.txt  /Users/noahgift/src/core_tools/test-folder/lev...

        """

        data = []
        #msg = "Generating Pandas DataFrame from folder: %s" % folder
        # LOG.info(msg)
        for root, _, files in os.walk(folder):
            for filename in files:
                fullpath = os.path.join(os.path.abspath(root), filename)
                file_, ext_ = os.path.splitext(filename)
                ext_ = ext_.lower()
                ts = self.get_creation_date(fullpath)
                birth_date = (datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d'))
                last_modified = os.path.getmtime(fullpath)
                try:
                    file_category = app_config()['ext_map'][ext_]
                except KeyError:
                    file_category = 'uncategorized'
                data.append((filename, fullpath, birth_date, last_modified, file_category))
        return pd.DataFrame(data, columns=['filename', 'fullpath', "creation_date", "last_modified", "file_category"])


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = ImportBrowser()
    td.setWindowTitle('Ingest-o-matic')
    td.show()
    td.raise_()
    app.exec_()

