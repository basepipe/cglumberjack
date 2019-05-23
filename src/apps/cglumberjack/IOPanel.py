import os
import shutil
import pandas as pd
import logging
import glob
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.dialog import InputDialog
from cglui.widgets.file_system import LJFileBrowser
from cglui.widgets.combo import AdvComboBox
from widgets import LJListWidget, EmptyStateWidget
from cglcore.config import app_config
from cglcore.path import PathObject, CreateProductionData


class EmptyStateWidgetIO(EmptyStateWidget):
    files_added = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        EmptyStateWidget.__init__(self, parent)
        self.path_object = path_object
        self.setText('Drag/Drop to Create a \nNew Import Version')
        self.setStyleSheet("background-color: white; border:1px dashed black;")

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


class IOPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        if path_object:
            self.path_object = path_object
        else:
            print 'No Path Object found, exiting'
            return

        self.path_object_next = None
        self.panel = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout()
        self.title = 'Import to %s' % path_object.project
        self.task = None
        self.version = '000.000'
        self.latest_version = '000.000'
        self.user = None
        self.resolution = None
        self.root = None
        self.company = None
        self.project = None
        self.data_frame = None

        self.path_object.set_attr(scope='IO')
        self.path_object.set_attr(ingest_source='*')
        self.data_frame = None
        self.pandas_path = ''
        self.io_statuses = ['Imported', 'Tagged', 'Published']

        self.file_tree = LJFileBrowser(self)
        self.file_tree.setMinimumHeight(200)
        self.file_tree.setMinimumWidth(800)

        self.source_widget = LJListWidget('Sources')
        self.import_events = LJListWidget('Previous Ingests')
        self.import_events.hide()

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
        self.empty_state = EmptyStateWidgetIO(path_object=self.path_object)
        self.empty_state.setText('Select a Source:\n Click + to Create a new one')
        # self.empty_state.hide()

        self.tags_title_row.addStretch(1)

        h_layout.addWidget(self.source_widget)
        h_layout.addWidget(self.import_events)
        self.panel.addLayout(h_layout)
        self.panel.addWidget(self.empty_state)
        self.panel.addWidget(self.file_tree)

        self.panel.addLayout(self.tags_title_row)
        self.panel.addLayout(self.radio_row)
        self.panel.addLayout(self.seq_row)
        self.panel.addLayout(self.tags_row)
        self.panel.addLayout(self.buttons_row)
        self.panel.addStretch(1)

        self.load_companies()
        self.hide_tags()
        self.file_tree.hide()

        self.shot_radio_button.clicked.connect(self.on_radio_clicked)
        self.asset_radio_button.clicked.connect(self.on_radio_clicked)
        self.seq_combo.currentIndexChanged.connect(self.on_seq_changed)
        self.file_tree.initialized.connect(self.load_data_frame)
        self.file_tree.selected.connect(self.on_client_file_selected)
        self.seq_combo.editTextChanged.connect(self.edit_data_frame)
        self.shot_combo.editTextChanged.connect(self.edit_data_frame)
        self.task_combo.editTextChanged.connect(self.edit_data_frame)
        self.tags_line_edit.textChanged.connect(self.edit_tags)
        self.source_widget.add_button.clicked.connect(self.on_source_add_clicked)
        self.source_widget.list.clicked.connect(self.on_company_changed)
        self.import_events.list.clicked.connect(self.on_event_selected)
        self.import_events.add_button.clicked.connect(self.on_add_ingest_event)
        self.publish_button.clicked.connect(self.publish_tagged_assets)
        self.empty_state.files_added.connect(self.new_files_dragged)

    def on_source_add_clicked(self):
        dialog = InputDialog(title='Add Source Company or Gear', message='Add an Import Source:', line_edit=True,
                             buttons=['Cancel', 'Add Source'])
        dialog.exec_()

        if dialog.button == 'Add Source':
            print "I'm creating a new source for you"

    def new_files_dragged(self, files):
        if self.path_object.ingest_source == '*':
            print 'Please Select An Ingest Source Before Dragging Files'
            return
        to_folder = self.path_object_next.path_root
        if not os.path.exists(to_folder):
            os.makedirs(to_folder)
        for f in files:
            file_ = os.path.split(f)[-1]
            to_file = os.path.join(to_folder, file_)
            if '.' in file_:
                logging.info('Copying File From %s to %s' % (f, to_file))
                shutil.copy2(f, to_file)
            else:
                logging.info('Copying Folder From %s to %s' % (f, to_file))
                shutil.copy(f, to_file)
        self.load_import_events()
        num = self.import_events.list.count()
        item = self.import_events.list.item(num - 1)
        item.setSelected(True)
        self.on_event_selected()

    def load_companies(self):
        self.source_widget.list.clear()
        dir_ = self.path_object.glob_project_element('ingest_source')
        if 'CLIENT' not in dir_:
            dir_.insert(0, 'CLIENT')
        self.source_widget.list.addItems(dir_)

    def on_company_changed(self):
        self.hide_tags()
        self.file_tree.hide()
        self.empty_state.show()
        self.source_widget.list.selectedItems()[-1].text()
        self.empty_state.setText('Drag Media Here to Create New Ingest Version')
        self.path_object.set_attr(ingest_source=self.source_widget.list.selectedItems()[-1].text())
        self.load_import_events()

    def load_import_events(self, select_latest=False):
        latest = '-001.000'
        self.import_events.list.clear()
        events = glob.glob('%s/%s' % (self.path_object.split_after('ingest_source'), '*'))
        if events:
            self.import_events.show()
            for e in events:
                self.import_events.list.addItem(os.path.split(e)[-1])
                # self.import_events.list.setItemSelected(item)
            latest = os.path.split(e)[-1]
        self.path_object.set_attr(version=latest)
        self.path_object_next = self.path_object.next_major_version()
        self.empty_state.setText('Drag Media Here to Create Ingest %s' % self.path_object_next.version)

    def on_event_selected(self):
        self.hide_tags()
        self.clear_all()
        self.path_object.set_attr(version=self.import_events.list.selectedItems()[-1].text())
        # Load the Tree Widget
        self.populate_tree()
        self.location_changed.emit(self.path_object)

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
        # deselect everything in the event
        # change the file path to reflect no selection
        self.hide_tags()
        self.file_tree.hide()
        self.empty_state.show()


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

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

