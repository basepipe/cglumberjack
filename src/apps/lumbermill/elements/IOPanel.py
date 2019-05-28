import os
import shutil
import pandas as pd
import logging
import glob
# noinspection PyUnresolvedReferences
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.dialog import InputDialog
from cglui.widgets.containers.tree import LJTreeWidget
from cglui.widgets.file_system import LJFileBrowser
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.widgets import LJListWidget, EmptyStateWidget
from cglcore.config import app_config
from cglcore.path import CreateProductionData, icon_path, list_dir


class EmptyStateWidgetIO(EmptyStateWidget):
    files_added = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        EmptyStateWidget.__init__(self, parent)
        self.path_object = path_object
        self.setText('Drag/Drop to Create a \nNew Import Version')
        self.setProperty('class', 'empty_state')

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


# noinspection PyPep8Naming,PyPep8Naming
class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self):
        return len(self._data.values)

    def columnCount(self):
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
        self.scope = 'shots'

        self.path_object.set_attr(scope='IO')
        self.path_object.set_attr(ingest_source='*')
        self.data_frame = None
        self.pandas_path = ''
        self.io_statuses = ['Imported', 'Tagged', 'Published']

        self.file_tree = LJTreeWidget(self, header_list=['Name', 'Type', 'Date Ingested', 'Status'])
        self.file_tree.setMinimumHeight(200)
        self.file_tree.setMinimumWidth(800)

        pixmap = QtGui.QPixmap(icon_path('back24px.png'))
        import_empty_icon = QtGui.QIcon(pixmap)

        self.source_widget = LJListWidget('Sources', pixmap=None)
        self.ingest_widget = LJListWidget('Ingests', pixmap=None, empty_state_text='Select Source',
                                          empty_state_icon=import_empty_icon)
        #self.import_events.hide()

        self.tags_title = QtWidgets.QLabel("<b>Select File(s) or Folder(s) to tag</b>")
        self.tags_title_row = QtWidgets.QHBoxLayout()
        self.tags_title_row.addWidget(self.tags_title)

        self.scope_label = QtWidgets.QLabel('Scope')
        self.scope_combo = AdvComboBox()
        self.scope_combo.addItems(['assets', 'shots'])
        self.seq_row = QtWidgets.QHBoxLayout()
        self.seq_row.addWidget(self.scope_label)
        self.seq_row.addWidget(self.scope_combo)

        self.seq_label = QtWidgets.QLabel('Seq ')
        self.seq_combo = AdvComboBox()

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
        self.publish_button = QtWidgets.QPushButton('Publish')
        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.hide()
        self.publish_button.setProperty('class', 'basic')
        self.refresh_button.setProperty('class', 'basic')
        self.buttons_row.addStretch(1)
        self.buttons_row.addWidget(self.refresh_button)
        self.buttons_row.addWidget(self.publish_button)
        self.empty_state = EmptyStateWidgetIO(path_object=self.path_object)
        self.empty_state.setText('Select a Source:\n Click + to Create a new one')
        self.empty_state.hide()

        self.tags_title_row.addStretch(1)

        h_layout.addWidget(self.source_widget)
        h_layout.addWidget(self.ingest_widget)
        self.panel.addLayout(h_layout)
        self.panel.addWidget(self.empty_state)
        self.panel.addWidget(self.file_tree)

        self.panel.addLayout(self.tags_title_row)
        self.panel.addLayout(self.seq_row)
        self.panel.addLayout(self.tags_row)
        self.panel.addLayout(self.buttons_row)
        self.panel.addStretch(1)

        self.load_companies()
        self.ingest_widget.empty_state.show()
        self.ingest_widget.list.hide()
        self.hide_tags()
        self.file_tree.hide()

        self.refresh_button.clicked.connect(self.on_ingest_selected)
        self.scope_combo.currentIndexChanged.connect(self.on_scope_changed)
        self.seq_combo.currentIndexChanged.connect(self.on_seq_changed)
        self.file_tree.selected.connect(self.on_client_file_selected)
        self.seq_combo.editTextChanged.connect(self.edit_data_frame)
        self.shot_combo.editTextChanged.connect(self.edit_data_frame)
        self.task_combo.editTextChanged.connect(self.edit_data_frame)
        self.tags_line_edit.textChanged.connect(self.edit_tags)
        self.source_widget.add_button.clicked.connect(self.on_source_add_clicked)
        self.source_widget.list.clicked.connect(self.on_source_selected)
        self.ingest_widget.list.clicked.connect(self.on_ingest_selected)
        self.ingest_widget.add_button.clicked.connect(self.on_add_ingest_event)
        self.publish_button.clicked.connect(self.publish_tagged_assets)
        self.empty_state.files_added.connect(self.new_files_dragged)
        self.on_scope_changed()

    @staticmethod
    def on_source_add_clicked():
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
        num = self.ingest_widget.list.count()
        item = self.ingest_widget.list.item(num - 1)
        item.setSelected(True)
        self.on_ingest_selected()

    def load_companies(self):
        self.source_widget.list.clear()
        dir_ = self.path_object.glob_project_element('ingest_source')
        if 'CLIENT' not in dir_:
            dir_.insert(0, 'CLIENT')
        self.source_widget.list.addItems(dir_)

    def on_source_selected(self):
        self.hide_tags()
        self.file_tree.hide()
        self.empty_state.show()
        self.source_widget.list.selectedItems()[-1].text()
        self.empty_state.setText('Drag Media Here \nto Create New Ingest Version')
        self.path_object.set_attr(ingest_source=self.source_widget.list.selectedItems()[-1].text())
        self.load_import_events()

    def load_import_events(self):
        latest = '-001.000'
        self.ingest_widget.list.clear()
        events = glob.glob('%s/%s' % (self.path_object.split_after('ingest_source'), '*'))
        if events:
            self.ingest_widget.empty_state.hide()
            self.ingest_widget.show()
            for e in events:
                self.ingest_widget.list.addItem(os.path.split(e)[-1])
                latest = os.path.split(e)[-1]
        else:
            self.ingest_widget.empty_state.show()
            self.ingest_widget.empty_state.setText("No Ingests")
            pixmap = QtGui.QPixmap(icon_path('axeWarning24px.png'))
            icon = QtGui.QIcon(pixmap)
            self.ingest_widget.set_icon(icon)
        self.path_object.set_attr(version=latest)
        self.path_object_next = self.path_object.next_major_version()
        self.empty_state.setText('Drag Media Here to Create Ingest %s' % self.path_object_next.version)

    def on_ingest_selected(self):
        self.ingest_widget.empty_state.hide()
        self.hide_tags()
        self.clear_all()
        self.path_object.set_attr(version=self.ingest_widget.list.selectedItems()[-1].text())
        # Load the Tree Widget
        self.populate_tree()
        self.load_data_frame()
        self.location_changed.emit(self.path_object)

    def populate_tree(self):
        self.file_tree.clear()
        if os.listdir(self.path_object.path_root):
            self.empty_state.hide()
            self.file_tree.show()
            self.file_tree.directory = self.path_object.path_root
            self.file_tree.populate_parents(list_dir(self.file_tree.directory, basename=True))
            print 'I should be showing the files from the directory'
            self.show_tags_gui()
            return
        else:
            self.file_tree.hide()
            self.hide_tags()
            self.empty_state.show()

    def load_data_frame(self):
        self.pandas_path = os.path.join(self.file_tree.directory, 'publish_data.csv')
        if os.path.exists(self.pandas_path):
            self.data_frame = pd.read_csv(self.pandas_path, names=["Filepath", "Tags", "Keep Client Naming", "Scope",
                                                                   "Seq", "Shot", "Task", "Project Filepath", "Status"])
        else:
            data = []
            # msg = "Generating Pandas DataFrame from folder: %s" % folder
            # LOG.info(msg)
            for root, _, files in os.walk(self.file_tree.directory):
                for filename in files:
                    fullpath = os.path.join(os.path.abspath(root), filename)
                    data.append((fullpath, '', True, '', '', '', '', '', self.io_statuses[0]))
            self.data_frame = pd.DataFrame(data, columns=["Filepath", "Tags", "Keep Client Naming", "Scope",
                                                          "Seq", "Shot", "Task", "Project Filepath", "Status"])
        self.save_data_frame()

    def save_data_frame(self):
        dropped_dupes = self.data_frame.drop_duplicates()
        dropped_dupes.to_csv(self.pandas_path)
        # self.on_ingest_selected()

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
        if self.seq_combo.currentText():
            seq = str(self.seq_combo.currentText())
            if self.shot_combo.currentText():
                shot = str(self.shot_combo.currentText())
                if self.task_combo.currentText():
                    try:
                        task = app_config()['pipeline_steps'][self.scope][str(self.task_combo.currentText())]
                        to_object = self.path_object.copy(scope=self.scope,
                                                          seq=seq,
                                                          shot=shot,
                                                          task=task,
                                                          context='render',
                                                          version='000.000',
                                                          user='publish',
                                                          resolution='high')
                        print 'Pub Path: %s' % to_object.path_root
                        for f in files:
                            f = f.replace('/', '\\')
                            row = self.data_frame.loc[self.data_frame['Filepath'] == f].index[0]
                            to_path = os.path.join(to_object.path_root, os.path.split(f)[-1])
                            self.data_frame.at[row, 'Scope'] = self.scope
                            self.data_frame.at[row, 'Seq'] = seq
                            self.data_frame.at[row, 'Shot'] = shot
                            self.data_frame.at[row, 'Task'] = task
                            self.data_frame.at[row, 'Project Filepath'] = to_path
                            self.data_frame.at[row, 'Status'] = self.io_statuses[1]
                        self.save_data_frame()
                    except KeyError:
                        print 'Error with something:'
                        print 'scope', self.scope
                        print 'seq', seq
                        print 'shot', shot
                        pass

    def clear_all(self):
        self.seq_combo.clear()
        self.shot_combo.clear()
        self.task_combo.clear()
        self.tags_line_edit.clear()

    def show_tags_info(self, data):
        """
        Shows all the information for the tags.
        :param data:
        :return:
        """
        self.tags_line_edit.clear()
        filepath = data[-1][0].replace('/', '\\')
        if data[-1][1] == 'sequence':
            print 'found a sequence, doing different'
        # if this is a sequence do something different.
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
            print data[-1]
            filepath = r'%s' % data[-1][0].replace('/', '\\')
            print filepath
            try:
                row = self.data_frame.loc[self.data_frame['Filepath'] == filepath].index[0]
                print row
                print self.data_frame.loc[row, 'Filepath']
            except IndexError:
                self.hide_tags()
                return
            seq = self.data_frame.loc[row, 'Seq']
            shot = self.data_frame.loc[row, 'Shot']
            task = self.data_frame.loc[row, 'Task']
            _ = self.data_frame.loc[row, 'Status']
            if type(seq) != float:
                if seq:
                    try:
                        seq = '%03d' % int(seq)
                        self.set_combo_to_text(self.seq_combo, seq)
                    except ValueError:
                        self.set_combo_to_text(self.seq_combo, seq)
            if type(shot) != float:
                if shot:
                    try:
                        shot = '%04d' % int(shot)
                        self.set_combo_to_text(self.shot_combo, shot)
                    except ValueError:
                        self.set_combo_to_text(self.shot_combo, shot)
            if type(task) != float:
                if task:
                    task = app_config()['pipeline_steps']['short_to_long'][task]
                    self.set_combo_to_text(self.task_combo, task)

    def hide_tags(self):
        self.tags_title.setText("<b>Select File(s) or Folder(s) to tag</b>")
        self.tags_title.hide()
        self.scope_label.hide()
        self.scope_combo.hide()
        self.seq_label.hide()
        self.seq_combo.hide()
        self.shot_label.hide()
        self.shot_combo.hide()
        self.task_label.hide()
        self.task_combo.hide()
        self.tags_label.hide()
        self.tags_line_edit.hide()
        self.publish_button.hide()

    def show_tags_gui(self, files=None):
        if not files:
            files_text = 'files'
        else:
            if len(files) == 1:
                files_text = files[0]
            else:
                files_text = '%s files' % len(files)

        self.tags_title.setText("<b>Tag %s for Publish</b>" % os.path.split(files_text)[-1])
        self.tags_title.show()
        self.scope_combo.show()
        self.scope_label.show()
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
        if self.scope == 'shots':
            element = 'seq'
        else:
            element = 'type'
        tasks = app_config()['pipeline_steps'][self.scope]
        seqs = self.path_object.copy(seq='*', scope=self.scope).glob_project_element(element)
        task_names = ['']
        for each in tasks:
            if each not in ignore:
                task_names.append(each)
        self.task_combo.addItems(sorted(task_names))
        seqs.insert(0, '')
        self.seq_combo.addItems(seqs)

    def on_scope_changed(self):
        self.scope = self.scope_combo.currentText()
        if self.scope == 'assets':
            self.seq_label.setText('Type')
            self.shot_label.setText('Asset')
        elif self.scope == 'shots':
            self.seq_label.setText('Seq ')
            self.shot_label.setText('Shot')


    def on_seq_changed(self):
        self.shot_combo.clear()
        scope = self.scope
        seq = self.seq_combo.currentText()
        if seq:
            _ = self.path_object.copy(scope=scope, seq=seq, shot='*')
            if self.scope == 'shots':
                shots = self.path_object.copy(scope=scope, seq=seq, shot='*').glob_project_element('shot')
            elif self.scope == 'assets':
                shots = self.path_object.copy(scope=scope, seq=seq, shot='*').glob_project_element('asset')
            if shots:
                shots.insert(0, '')
                self.shot_combo.addItems(shots)

    def on_client_file_selected(self, data):
        files = []
        print data
        for row in data:
            fname = row[0]
            type_ = row[1]
            if type_ == 'sequence':
                print 'Have to do something special for these'
            path_, filename_ = os.path.split(fname)
            files.append(filename_)
        self.seq_combo.clear()
        self.shot_combo.clear()
        self.task_combo.clear()
        self.tags_line_edit.clear()
        self.sender().parent().populate_combos()
        self.sender().parent().show_combo_info(data)
        self.sender().parent().show_tags_gui(files=files)
        self.sender().parent().show_tags_info(data)

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

