import platform
import os
import psutil
import datetime
import pandas as pd
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJDialog
from cglui.widgets.dialog import InputDialog
from cglui.widgets.project_selection_module import LineEditWidget, LabelEditRow, ProjectControlCenter, LabelComboRow
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
        self.current_location = {}

        header = self.destination_tree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.destination_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.dest_path = LineEditWidget(label='Destination')
        self.category = LineEditWidget(label='Category', read_only=False)
        self.category.line_edit.setText('ingestion')

        self.files_column = QtWidgets.QVBoxLayout()
        self.files_column.addWidget(self.category)
        self.files_column.addWidget(self.dest_path)
        self.files_column.addWidget(self.destination_tree)

        # self.destination_tree.header().hide()
        self.h_layout = QtWidgets.QHBoxLayout()
        self.data_frame = pd.DataFrame()
        self.media_column = QtWidgets.QVBoxLayout()
        self.media_internal = QtWidgets.QLabel('Internal Media')
        self.media_label = QtWidgets.QLabel('Connected Media')
        self.media_sources = QtWidgets.QListWidget()
        self.media_sources.setMinimumWidth(200)
        self.media_sources.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.media_sources.setEnabled(False)
        self.control_center = ProjectControlCenter()
        self.control_center.hide_filters()

        self.media_column.addWidget(self.media_label)
        self.media_column.addWidget(self.media_sources)

        self.project_info_column = QtWidgets.QVBoxLayout()
        self.ingest_button = QtWidgets.QPushButton()
        self.ingest_button.setText('Ingest')
        self.source_dict = {}

        self.capture_date = LabelEditRow("Capture Date")
        self.uncategorized_files = QtWidgets.QLabel("0 Uncategorized Files")
        # TODO - i want drop down menus for tasks for each of these file types so i know where they're all going.

        self.project_info_column.addWidget(self.control_center)
        self.files_column.addWidget(self.ingest_button)

        self.date_list = QtWidgets.QListWidget()
        self.file_list = QtWidgets.QListWidget()
        self.h_layout.addLayout(self.project_info_column)
        self.h_layout.addLayout(self.media_column)
        self.h_layout.addLayout(self.files_column)

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
        self.ingest_button.hide()
        self.dest_path.hide_all()
        self.category.hide_all()
        self.destination_tree.hide()

    def show_right_column(self):
        self.ingest_button.show()
        self.dest_path.show_all()
        self.category.show_all()
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

    def on_category_changed(self):
        self.current_location['seq'] = self.category.line_edit.text()
        self.dest_path.line_edit.setText(PathObject(self.current_location).path_root)

    def on_create_project_clicked(self):
        print 'create project'

    def populate_tree(self):
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Source')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Destination')
        self.destination_tree.setModel(model)
        self.destination_tree.setMinimumWidth(600)
        model.removeRows(0, model.rowCount())
        for date in sorted(self.data_frame.creation_date.unique()):
            # Add all the date to the tree widget
            date_object = QtGui.QStandardItem(str(date))
            date_object.setEditable(False)
            model.appendRow(date_object)
            for each in sorted(self.data_frame.file_category.unique()):
                fc_object = QtGui.QStandardItem(str(each))
                fc_object.setEditable(False)
                date_object.appendRow(fc_object)
                # return list of file names that match the date and the category
                df = self.data_frame[(self.data_frame['file_category'] == each) & (self.data_frame['creation_date'] == date)]
                for file_ in sorted(df.fullpath.tolist()):
                    dir_, file_ = os.path.split(file_)
                    self.current_location['shot'] = str(date)
                    self.current_location['filename'] = file_
                    self.current_location['task'] = 'audio'
                    self.current_location['resolution'] = 'high'
                    self.current_location['user'] = 'tmikota'
                    path_object = PathObject(self.current_location)
                    path_root = path_object.path_root
                    path_root = path_root.split(self.category.line_edit.text())[-1]
                    file_object = QtGui.QStandardItem(str(file_))
                    file_object.setEditable(False)
                    fc_dest = QtGui.QStandardItem(path_root)
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
        self.source_dict = {}
        self.data_frame = pd.DataFrame
        dframes = []
        if self.media_sources.selectedItems():
            for each in self.media_sources.selectedItems():
                df = self.local_tree_dataframe(each.text())
                self.source_dict[each.text()] = df
            for key in self.source_dict:
                dframes.append(self.source_dict[key])
            if dframes:
                self.data_frame = pd.concat(dframes)
                self.date_list.addItems(sorted(df.creation_date.unique()))
                self.populate_tree()
                self.show_right_column()
        else:
            print 'Nothing Selected'
            self.hide_right_column()

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
        self.current_location = {'root': self.control_center.root,
                                 'company': self.control_center.company,
                                 'context': 'source',
                                 'project': self.project,
                                 'scope': 'assets',
                                 'seq': self.category.line_edit.text()
                                 }
        self.dest_path.line_edit.setText(PathObject(self.current_location).path_root)


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

