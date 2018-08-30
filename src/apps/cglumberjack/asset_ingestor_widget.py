import os
import glob
from Qt import QtWidgets, QtCore, QtGui
from core.path import PathObject, CreateProductionData
from cglui.widgets.combo import AdvComboBox
from core.config import app_config
from cglcore.path import icon_path, create_production_data
import shutil


class AssetIngestTable(QtWidgets.QTableWidget):
    files_added_signal = QtCore.Signal(basestring)

    def __init__(self, parent=None):
        QtWidgets.QTableWidget.__init__(self, parent)
        self.setAcceptDrops(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

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
            self.files_added_signal.emit(file_list)
        else:
            e.ignore()


class AssetIngestor(QtWidgets.QDialog):
    def __init__(self, parent=None, path_dict=None, current_user=None):
        QtWidgets.QDialog.__init__(self)
        self.path_dict = {}
        self.current_user = current_user
        self.icon_path = os.path.join(icon_path(), 'folder2.png')
        self.setWindowTitle('File Ingestor')
        layout = QtWidgets.QVBoxLayout()
        if not path_dict:
            self.path_dict['root'] = 'D:'
            self.path_dict['company'] = 'cgl-blobgroup'
            self.path_dict['project'] = 'blobtown'
            self.path_dict['scope'] = 'assets'
            self.path_dict['context'] = 'source'
            self.path_dict['user'] = 'tmiko'
            self.path_dict['seq'] = ''
            self.path_dict['shot'] = ''
            self.path_dict['resolution'] = 'high'
            self.path_dict['version'] = '000.000'
        else:
            self.path_dict['root'] = path_dict['root']
            self.path_dict['company'] = path_dict['company']
            self.path_dict['project'] = path_dict['project']
            self.path_dict['scope'] = 'assets'
            self.path_dict['context'] = 'source'
            self.path_dict['seq'] = ''
            self.path_dict['shot'] = ''
            self.path_dict['resolution'] = 'high'
            self.path_dict['user'] = self.current_user
            self.path_dict['version'] = '000.000'
        print self.path_dict

        self.table = AssetIngestTable()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(['File', 'Scope', 'Seq/Category', 'Shot/Name', 'Task', 'From Path',
                                              'To Path', 'Ready'])
        self.table.verticalHeader().hide()
        self.scope_list = ["assets", "shots"]
        self.table.files_added_signal.connect(self.on_files_added)
        self.h_layout = QtWidgets.QHBoxLayout()
        self.ingest_button = QtWidgets.QPushButton('Ingest')
        self.ingest_button.setEnabled(False)
        self.h_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                    QtWidgets.QSizePolicy.Minimum))
        self.h_layout.addWidget(self.ingest_button)

        layout.addWidget(self.table)
        layout.addLayout(self.h_layout)
        self.setLayout(layout)

        self.ingest_button.clicked.connect(self.on_ingest_clicked)

    def on_files_added(self, data):
        # figure out how many rows in the current table
        self.table.setRowCount(len(data))
        for i, d in enumerate(data):
            dir_, file_ = os.path.split(d)
            file_item = QtWidgets.QTableWidgetItem(file_)
            folder_icon = QtWidgets.QIcon(self.icon_path)
            if os.path.isdir(d):
                file_item.setIcon(folder_icon)
            from_path_item = QtWidgets.QTableWidgetItem(d)
            scope_combo = AdvComboBox()
            scope_combo.addItems(self.scope_list)
            seq_combo = AdvComboBox()
            seq_combo.label = 'seq_combo'
            shot_combo = AdvComboBox()
            shot_combo.label = 'shot_combo'
            task_combo = AdvComboBox()
            task_combo.label = 'task_combo'
            to_path_item = QtWidgets.QTableWidgetItem('')
            ready_value = QtWidgets.QTableWidgetItem('False')

            self.table.setItem(i, 0, file_item)
            scope_combo.column = 1
            scope_combo.row = i
            scope_combo.task_widget = task_combo
            scope_combo.seq_widget = seq_combo
            seq_combo.shot_widget = shot_combo
            seq_combo.column = 2
            seq_combo.row = i
            task_combo.row = i
            task_combo.column = 4
            shot_combo.column = 3
            shot_combo.row = i

            self.table.setCellWidget(i, 1, scope_combo)
            self.table.setCellWidget(i, 2, seq_combo)
            self.table.setCellWidget(i, 3, shot_combo)
            self.table.setCellWidget(i, 4, task_combo)
            self.table.setItem(i, 5, from_path_item)
            self.table.setItem(i, 6, to_path_item)
            self.table.setItem(i, 7, ready_value)

            self.populate_tasks(task_combo)
            self.populate_seq(seq_combo)
            self.update_to_path(i)
            scope_combo.currentIndexChanged.connect(self.on_combo_changed)
            task_combo.currentIndexChanged.connect(self.on_combo_changed)
            seq_combo.currentIndexChanged.connect(self.on_combo_changed)
            shot_combo.currentIndexChanged.connect(self.on_combo_changed)
            shot_combo.editTextChanged.connect(self.on_combo_changed)
            self.table.resizeColumnsToContents()
            self.setTableWidth()

    def on_combo_changed(self):
        text = self.sender().currentText()
        if self.sender().column == 1:
            self.path_dict['scope'] = text
            self.populate_tasks(self.sender().task_widget)
            self.populate_seq(self.sender().seq_widget)
            # if it's a scope we'll fill the seq and the task combos
        if self.sender().column == 2:
            self.path_dict['seq'] = text
            self.populate_shot(self.sender().shot_widget)
        if self.sender().column == 3:
            self.path_dict['shot'] = text
        if self.sender().column == 4:
            self.path_dict['task'] = text
        self.update_to_path(self.sender().row)

    def update_to_path(self, row):
        path_obj = PathObject(self.path_dict)
        path_ = path_obj.path_root
        print path_, 'tom likes this'
        if self.pass_path_check():
            self.table.item(row, 6).setForeground(QtGui.QColor(0, 255, 0))
            self.table.item(row, 0).setForeground(QtGui.QColor(0, 255, 0))
            self.table.item(row, 7).setText('True')
        else:
            self.table.item(row, 6).setForeground(QtGui.QColor(255, 0, 0))
            self.table.item(row, 0).setForeground(QtGui.QColor(255, 0, 0))
            self.table.item(row, 7).setText('False')
        self.table.item(row, 6).setText(path_)
        self.table.resizeColumnsToContents()
        self.setTableWidth()
        self.ingest_path_preflight()

    def pass_path_check(self):
        try:
            list_ = [self.path_dict['scope'],
                     self.path_dict['seq'],
                     self.path_dict['shot'],
                     self.path_dict['task'],
                     ]
            if '' in list_:
                return False
            elif '*' in list_:
                return False
            elif None in list_:
                return False
            else:
                return True
        except KeyError:
            return False

    def populate_tasks(self, task_widget):
        scope = self.path_dict['scope']
        task_list = app_config()['pipeline_steps'][scope]
        tasks = ['']
        task_widget.clear()
        for each in task_list:
            tasks.append(task_list[each])
        task_widget.addItems(tasks)

    def populate_seq(self, widget):
        widget.clear()
        self.path_dict['seq'] = '*'
        if self.path_dict['scope'] == 'assets':
            asset_categories = app_config()['asset_categories']
            for full_name in asset_categories:
                widget.addItem(asset_categories[full_name])
        if self.path_dict['scope'] == 'shots':
            seq = PathObject(self.path_dict).glob_project_element('seq')
            if seq:
                widget.addItems(seq)
        self.path_dict['seq'] = widget.currentText()
        self.update_to_path(widget.row)
        self.populate_shot(widget.shot_widget)

    def populate_shot(self, widget):
        widget.clear()
        widget.addItem('')
        self.path_dict['shot'] = '*'
        shots = PathObject(self.path_dict).glob_project_element('shot')
        widget.addItems(shots)
        self.path_dict['shot'] = widget.currentText()
        self.update_to_path(widget.row)

    def setTableWidth(self):
        width = self.table.verticalHeader().width()
        width += self.table.horizontalHeader().length()
        if self.table.verticalScrollBar().isVisible():
            width += self.table.verticalScrollBar().width()
        width += self.table.frameWidth() * 2
        self.table.setFixedWidth(width)

    def resizeEvent(self, event):
        self.setTableWidth()
        super(AssetIngestor, self).resizeEvent(event)

    def ingest_path_preflight(self):
        # check each row, 7 for True/False and enable the ingest button if they pass
        for i in range(self.table.rowCount()):
            if self.table.item(i, 7):
                if self.table.item(i, 7).text() == 'False':
                    self.ingest_button.setEnabled(False)
                else:
                    self.ingest_button.setEnabled(True)

    def on_ingest_clicked(self):
        for i in range(self.table.rowCount()):
            from_ = self.table.item(i, 5).text()
            filename = self.table.item(i, 0).text()
            to_folder = str(self.table.item(i, 6).text())
            to_object = PathObject(to_folder)
            next_version = to_object.new_major_version_object()
            next_version.new_set_attr(filename=filename)
            CreateProductionData(next_version.data)
            print('copying %s -> %s' % (from_, next_version.path_root))
            shutil.copy2(from_, next_version.path_root)
            self.accept()


if __name__ == '__main__':
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = AssetIngestor()
    td.setWindowTitle('Multi-Ingestor')
    td.show()
    td.raise_()
    app.exec_()
