import os
import shutil
import pandas as pd
import logging
import glob
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJDialog
from cglui.widgets.file_system import LJFileBrowser
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.project_selection_module import LJListWidget
from cglcore.config import app_config
from cglcore.path import PathObject, CreateProductionData


class EmptyStateWidget(QtWidgets.QPushButton):
    files_added = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QPushButton.__init__(self, parent)
        self.path_object = path_object
        self.setAcceptDrops(True)
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
        self.setText('Drag/Drop to Add Files')
        self.setStyleSheet("background-color: white; border:1px dashed black;")
        self.to_path = ''

    def mouseReleaseEvent(self, e):
        super(EmptyStateWidget, self).mouseReleaseEvent(e)

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
        new_obj = self.path_object.copy()
        self.to_path = new_obj.path_root
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

    def __init__(self, parent=None, path_object=None):
        super(ImportBrowser, self).__init__()
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout()
        if path_object:
            self.path_object = path_object
        else:
            print 'No Path Object found, exiting'
            return
        self.title = 'Import to %s' % path_object.project

        self.task = None
        self.version = None
        self.user = None
        self.resolution = None
        self.root = None
        self.company = None
        self.project = None
        self.data_frame = None

        self.path_object.set_attr(scope='IO')
        self.path_object.set_attr(input_company='*')
        self.data_frame = None
        self.pandas_path = ''
        self.io_statuses = ['Imported', 'Tagged', 'Published']

        self.file_tree = LJFileBrowser(self)
        self.file_tree.setMinimumHeight(200)
        self.file_tree.setMinimumWidth(800)

        self.company_widget = LJListWidget('Import Sources')
        self.import_events = LJListWidget('Import Versions')

        self.tags_title = QtWidgets.QLabel("<b>Select File(s) or Folder(s) to tag</b>")
        self.tags_title_row = QtWidgets.QHBoxLayout()
        self.tags_title_row.addWidget(self.tags_title)

        self.shot_radio_button = QtWidgets.QRadioButton('Shots')
        self.shot_radio_button.setChecked(True)
        self.asset_radio_button = QtWidgets.QRadioButton('Assets')
        self.radio_row = QtWidgets.QHBoxLayout()

        self.radio_row.addWidget(self.shot_radio_button)
        self.radio_row.addWidget(self.asset_radio_button)
        self.radio_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                     QtWidgets.QSizePolicy.Minimum))

        self.seq_label = QtWidgets.QLabel('Seq ')
        self.seq_combo = AdvComboBox()
        self.seq_row = QtWidgets.QHBoxLayout()
        self.seq_row.addWidget(self.seq_label)
        self.seq_row.addWidget(self.seq_combo)

        self.shot_label = QtWidgets.QLabel('Shot')
        self.shot_combo = AdvComboBox()
        self.seq_row.addWidget(self.shot_label)
        self.seq_row.addWidget(self.shot_combo)

        self.task_label = QtWidgets.QLabel('Task')
        self.task_combo = AdvComboBox()
        self.seq_row.addWidget(self.task_label)
        self.seq_row.addWidget(self.task_combo)

        self.tags_label = QtWidgets.QLabel("Tags")
        self.tags_label.setWordWrap(True)
        self.tags_label.setMaximumWidth(100)
        self.tags_line_edit = QtWidgets.QLineEdit()
        self.tags_row = QtWidgets.QHBoxLayout()
        self.tags_row.addWidget(self.tags_label)
        self.tags_row.addWidget(self.tags_line_edit)
        # create buttons row
        self.buttons_row = QtWidgets.QHBoxLayout()
        self.publish_button = QtWidgets.QPushButton('Publish Tagged')
        self.buttons_row.addStretch(1)
        self.buttons_row.addWidget(self.publish_button)
        self.empty_state = EmptyStateWidget(path_object=self.path_object)
        self.empty_state.hide()

        self.tags_title_row.addStretch(1)

        h_layout.addWidget(self.company_widget)
        h_layout.addWidget(self.import_events)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.empty_state)
        v_layout.addWidget(self.file_tree)

        v_layout.addLayout(self.tags_title_row)
        v_layout.addLayout(self.radio_row)
        v_layout.addLayout(self.seq_row)
        v_layout.addLayout(self.tags_row)
        v_layout.addLayout(self.buttons_row)
        v_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                               QtWidgets.QSizePolicy.Expanding))

        self.load_companies()
        self.hide_tags()
        self.file_tree.hide()

        self.import_events.add_button.clicked.connect(self.on_add_ingest_event)
        self.shot_radio_button.clicked.connect(self.on_radio_clicked)
        self.asset_radio_button.clicked.connect(self.on_radio_clicked)
        self.seq_combo.currentIndexChanged.connect(self.on_seq_changed)
        self.file_tree.initialized.connect(self.load_data_frame)
        self.file_tree.selected.connect(self.on_client_file_selected)
        self.seq_combo.editTextChanged.connect(self.edit_data_frame)
        self.shot_combo.editTextChanged.connect(self.edit_data_frame)
        self.task_combo.editTextChanged.connect(self.edit_data_frame)
        self.tags_line_edit.textChanged.connect(self.edit_tags)
        self.company_widget.list.clicked.connect(self.on_company_changed)
        self.import_events.list.clicked.connect(self.on_event_selected)
        self.publish_button.clicked.connect(self.publish_tagged_assets)
        self.empty_state.files_added.connect(self.new_files_dragged)

    def new_files_dragged(self, files):
        for f in files:
            file_ = os.path.split(f)[-1]
            to_object = PathObject(self.sender().to_path)
            to_folder = to_object.path_root
            to_file = os.path.join(to_folder, file_)
            if '.' in file_:
                logging.info('Copying File From %s to %s' % (f, to_file))
                shutil.copy2(f, to_file)
            else:
                logging.info('Copying Folder From %s to %s' % (f, to_file))
                shutil.copy(f, to_file)
        self.on_event_selected()

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
        self.path_object.set_attr(version='000.0000')
        self.load_import_events()

    def load_import_events(self):
        latest = '-001.000'
        self.import_events.list.clear()
        events = glob.glob('%s/%s' % (self.path_object.split_after('input_company'), '*'))
        for e in events:
            latest = os.path.split(e)[-1]
            self.import_events.list.addItem(os.path.split(e)[-1])
        self.path_object.set_attr(version=latest)

    def on_event_selected(self):
        self.hide_tags()
        self.clear_all()
        self.path_object.set_attr(version=self.import_events.list.selectedItems()[-1].text())
        # Load the Tree Widget
        self.populate_tree()

    def populate_tree(self):
        if os.listdir(self.path_object.path_root):
            self.empty_state.hide()
            self.file_tree.show()
            self.file_tree.populate(directory=self.path_object.path_root)
            self.show_tags()
        else:
            self.file_tree.hide()
            self.hide_tags()
            self.empty_state.show()

    def load_data_frame(self):
        self.pandas_path = os.path.join(self.file_tree.directory, 'publish_data.csv')
        if os.path.exists(self.pandas_path):
            self.data_frame = pd.read_csv(self.pandas_path, names=["Filepath", "Tags", "Keep Client Naming",
                                                                   "Seq", "Shot", "Task", "Project Filepath", "Status"])
        else:
            data = []
            # msg = "Generating Pandas DataFrame from folder: %s" % folder
            # LOG.info(msg)
            for root, _, files in os.walk(self.file_tree.directory):
                for filename in files:
                    fullpath = os.path.join(os.path.abspath(root), filename)
                    data.append((fullpath, '', True, '', '', '', '', self.io_statuses[0]))
            self.data_frame = pd.DataFrame(data, columns=["Filepath", "Tags", "Keep Client Naming",
                                                          "Seq", "Shot", "Task",
                                                          "Project Filepath", "Status"])

    def save_data_frame(self):
        dropped_dupes = self.data_frame.drop_duplicates()
        dropped_dupes.to_csv(self.pandas_path)
        self.on_event_selected()

    def edit_tags(self):
        files = self.file_tree.selected_items
        tags = self.tags_line_edit.text()
        if tags:
            for f in files:
                f = f.replace('/', '\\')
                row = self.data_frame.loc[self.data_frame['Filepath'] == f].index[0]
                self.data_frame.at[row, 'Tags'] = tags
            self.save_data_frame()

    def edit_data_frame(self):
        files = self.file_tree.selected_items
        if self.shot_radio_button.isChecked():
            scope = 'shots'
        elif self.asset_radio_button.isChecked():
            scope = 'assets'
        if self.seq_combo.currentText():
            seq = str(self.seq_combo.currentText())
            if self.shot_combo.currentText():
                shot = str(self.shot_combo.currentText())

                if self.task_combo.currentText():
                    try:
                        task = app_config()['pipeline_steps'][scope][str(self.task_combo.currentText())]
                        to_object = self.path_object.copy(scope=scope,
                                                          seq=seq,
                                                          shot=shot,
                                                          task=task,
                                                          context='render',
                                                          version='000.000',
                                                          user='publish',
                                                          resolution='high')
                        for f in files:
                            f = f.replace('/', '\\')
                            row = self.data_frame.loc[self.data_frame['Filepath'] == f].index[0]
                            to_path = os.path.join(to_object.path_root, os.path.split(f)[-1])
                            self.data_frame.at[row, 'Seq'] = seq
                            self.data_frame.at[row, 'Shot'] = shot
                            self.data_frame.at[row, 'Task'] = task
                            self.data_frame.at[row, 'Project Filepath'] = to_path
                            self.data_frame.at[row, 'Status'] = self.io_statuses[1]
                        self.save_data_frame()
                    except KeyError:
                        pass

    def clear_all(self):
        self.shot_combo.clear()
        self.seq_combo.clear()
        self.task_combo.clear()
        self.tags_line_edit.clear()

    def show_line_edit_info(self, data):
        self.tags_line_edit.clear()
        filepath = data[-1].replace('/', '\\')
        row = self.data_frame.loc[self.data_frame['Filepath'] == filepath].index[0]
        tags = self.data_frame.loc[row, 'Tags']
        if type(tags) != float:
            if tags:
                self.tags_line_edit.setText(tags)

    def set_combo_to_text(self, combo, text):
        index = combo.findText(text)
        if index != -1:
            combo.setCurrentIndex(index)
        else:
            combo.addItem(text)
            self.set_combo_to_text(combo, text)

    def show_combo_info(self, data):
        if data:
            print data
            filepath = data[-1].replace('/', '\\')
            row = self.data_frame.loc[self.data_frame['Filepath'] == filepath].index[0]
            seq = self.data_frame.loc[row, 'Seq']
            shot = self.data_frame.loc[row, 'Shot']
            task = self.data_frame.loc[row, 'Task']
            status = self.data_frame.loc[row, 'Status']
            if type(seq) != float:
                if seq:
                    seq = '%03d' % int(seq)
                    self.set_combo_to_text(self.seq_combo, seq)
            if type(shot) != float:
                if shot:
                    shot = '%04d' % int(shot)
                    self.set_combo_to_text(self.shot_combo, shot)
            if type(task) != float:
                if task:
                    task = app_config()['pipeline_steps']['short_to_long'][task]
                    self.set_combo_to_text(self.task_combo, task)

    def on_radio_clicked(self):
        self.clear_all()
        if self.shot_radio_button.isChecked():
            self.seq_label.setText('Seq ')
            self.shot_label.setText('Shot')
            self.tags_label.setText('Tags')
        if self.asset_radio_button.isChecked():
            self.seq_label.setText('Category')
            self.shot_label.setText('Asset')
            self.tags_label.setText('Tags        ')
        self.populate_combos()

    def hide_tags(self):
        self.tags_title.setText("<b>Select File(s) or Folder(s) to tag</b>")
        self.tags_title.hide()
        self.asset_radio_button.hide()
        self.shot_radio_button.hide()
        self.seq_label.hide()
        self.seq_combo.hide()
        self.shot_label.hide()
        self.shot_combo.hide()
        self.task_label.hide()
        self.task_combo.hide()
        self.tags_label.hide()
        self.tags_line_edit.hide()
        self.publish_button.hide()

    def show_tags(self, files=None):
        if not files:
            files_text = 'files'
        else:
            if len(files) == 1:
                files_text = files[0]
            else:
                files_text = '%s files' % len(files)

        self.tags_title.setText("<b>Tag %s for Publish</b>" % os.path.split(files_text)[-1])
        self.tags_title.show()
        self.asset_radio_button.show()
        self.shot_radio_button.show()
        self.seq_label.show()
        self.seq_combo.show()
        self.shot_label.show()
        self.shot_combo.show()
        self.task_label.show()
        self.task_combo.show()
        self.tags_label.show()
        self.tags_line_edit.show()
        self.publish_button.show()

    def populate_combos(self):
        ignore = ['default_steps', '']
        if self.shot_radio_button.isChecked():
            scope = 'shots'
        else:
            scope = 'assets'
        tasks = app_config()['pipeline_steps'][scope]
        seqs = self.path_object.copy(seq='*', scope=scope).glob_project_element('seq')
        task_names = ['']
        for each in tasks:
            if each not in ignore:
                task_names.append(each)
        self.task_combo.addItems(sorted(task_names))
        seqs.insert(0, '')
        self.seq_combo.addItems(seqs)

    def on_seq_changed(self):
        self.shot_combo.clear()
        if self.shot_radio_button.isChecked():
            scope = 'shots'
        else:
            scope = 'assets'
        seq = self.seq_combo.currentText()
        if seq:
            this = self.path_object.copy(scope=scope, seq=seq, shot='*')
            shots = self.path_object.copy(scope=scope, seq=seq, shot='*').glob_project_element('shot')
            if shots:
                shots.insert(0, '')
                self.shot_combo.addItems(shots)

    def on_client_file_selected(self, data):
        files = []
        for each in data:
            path_, filename_ = os.path.split(each)
            files.append(filename_)
        self.sender().parent().clear_all()
        self.sender().parent().show_tags(files=files)
        self.sender().parent().populate_combos()
        self.sender().parent().show_combo_info(data)
        self.sender().parent().show_line_edit_info(data)

    def on_add_ingest_event(self):
        version = self.path_object.next_major_version()
        print version.path_root
        if not os.path.exists(version.path_root):
            print 'Creating Version at: %s' % version.path_root
            os.makedirs(version.path_root)
        self.on_company_changed()
        # self.populate_tree()

    def publish_tagged_assets(self):
        # TODO - We need to be changing status to 'Published' on this.
        # TODO - I need to create a .txt file in the src directory detailing this publish
        for index, row in self.data_frame.iterrows():
            if row['Status'] == 'Tagged':
                from_file = row['Filepath']
                to_file = row['Project Filepath']
                if os.path.splitext(to_file)[-1]:
                    dir_ = os.path.dirname(to_file)
                else:
                    dir_ = to_file
                if not os.path.exists(dir_):
                    print 'Making Dirs: %s' % dir_
                    os.makedirs(dir_)
                if not os.path.exists(to_file):
                    print 'Copying %s to %s' % (from_file, to_file)
                    CreateProductionData(to_file)
                    shutil.copy2(from_file, to_file)
                row['Status'] = 'Published'
        self.save_data_frame()
        self.populate_tree()


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = ImportBrowser()
    td.setWindowTitle('Ingest-o-matic')
    td.show()
    td.raise_()
    app.exec_()