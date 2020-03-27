import os
import pandas as pd
import logging
import glob
import threading
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.progress_gif import ProgressGif
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.containers.tree import LJTreeWidget
from cgl.ui.widgets.combo import AdvComboBox
from cgl.ui.widgets.widgets import LJListWidget, EmptyStateWidget
from cgl.core.config import app_config
from cgl.core.path import PathObject, icon_path, lj_list_dir, split_sequence_frange, get_file_type
from plugins.preflight.main import Preflight
from panels import clear_layout
import time

CONFIG = app_config()
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


class EmptyStateWidgetIO(EmptyStateWidget):
    files_added = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        EmptyStateWidget.__init__(self, parent)
        self.setText('Drag/Drop to Create a \nNew Import Version')
        self.setProperty('class', 'empty_state')

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
            self.files_added.emit(file_list)
        else:
            e.ignore()


class IOPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        if path_object:
            self.path_object = path_object
        else:
            print 'No Path Object found, exiting'
            return
        self.project_management = CONFIG['account_info']['project_management']
        self.schema = CONFIG['project_management'][self.project_management]['api']['default_schema']
        self.schema_dict = CONFIG['project_management'][self.project_management]['tasks'][self.schema]
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
        self.width_hint = 1300
        self.height_hint = 1200
        self.current_selection = None

        self.path_object.set_attr(scope='IO')
        self.path_object.set_attr(ingest_source='*')
        self.data_frame = None
        self.pandas_path = ''
        self.io_statuses = ['Imported', 'Tagged', 'Published']

        self.file_tree = LJTreeWidget(self)
        #self.width_hint = self.file_tree.width_hint

        pixmap = QtGui.QPixmap(icon_path('back24px.png'))
        import_empty_icon = QtGui.QIcon(pixmap)

        self.source_widget = LJListWidget('Sources', pixmap=None)
        self.ingest_widget = LJListWidget('Ingests', pixmap=None, empty_state_text='Select Source',
                                          empty_state_icon=import_empty_icon)
        # self.import_events.hide()f

        self.tags_title = QtWidgets.QLineEdit("<b>Select File(s) or Folder(s) to tag</b>")
        self.tags_title.setReadOnly(True)
        self.tags_title.setProperty('class', 'feedback')
        self.tags_button = QtWidgets.QPushButton('View Publish')
        self.tags_button.setProperty('class', 'basic')
        self.tags_button.setMaximumWidth(180)
        self.tags_title_row = QtWidgets.QHBoxLayout()
        self.tags_title_row.addWidget(self.tags_title)
        self.tags_title_row.addWidget(self.tags_button)
        self.tags_button.hide()

        self.scope_label = QtWidgets.QLabel('Scope')
        self.scope_combo = AdvComboBox()
        self.scope_combo.addItems(['', 'assets', 'shots'])
        self.seq_row = QtWidgets.QHBoxLayout()
        self.seq_row.addWidget(self.scope_label)
        self.seq_row.addWidget(self.scope_combo)
        self.feedback_area = QtWidgets.QLabel('')

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
        self.task_combo.setEditable(False)
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

        self.publish_button = QtWidgets.QPushButton('Publish Selected')
        self.view_in_lumbermill = QtWidgets.QPushButton('View in Lumbermill')
        self.view_in_lumbermill.setMinimumWidth(220)
        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.hide()
        self.publish_button.setProperty('class', 'basic')
        self.view_in_lumbermill.setProperty('class', 'basic')
        self.refresh_button.setProperty('class', 'basic')
        self.buttons_row.addStretch(1)
        self.buttons_row.addWidget(self.refresh_button)
        self.buttons_row.addWidget(self.view_in_lumbermill)
        self.buttons_row.addWidget(self.publish_button)
        self.empty_state = EmptyStateWidgetIO(path_object=self.path_object)
        self.empty_state.setText('Select a Source:\n Click + to Create a new one')

        self.progress_bar = ProgressGif()
        self.progress_bar.hide()
        self.view_in_lumbermill.hide()

        h_layout.addWidget(self.source_widget)
        h_layout.addWidget(self.ingest_widget)
        self.panel.addLayout(h_layout)
        self.panel.addWidget(self.file_tree)
        self.panel.addWidget(self.empty_state)
        self.panel.addLayout(self.tags_title_row)
        self.panel.addWidget(self.progress_bar)
        self.panel.addLayout(self.seq_row)
        self.panel.addLayout(self.tags_row)
        self.panel.addLayout(self.buttons_row)
        self.panel.addWidget(self.feedback_area)
        self.panel.addStretch(1)

        self.load_companies()
        self.ingest_widget.empty_state.show()
        self.ingest_widget.list.hide()
        self.hide_tags()
        self.file_tree.hide()

        self.view_in_lumbermill.clicked.connect(self.on_view_in_lumbermill_clicked)
        self.refresh_button.clicked.connect(self.on_ingest_selected)
        self.scope_combo.currentIndexChanged.connect(self.on_scope_changed)
        self.seq_combo.currentIndexChanged.connect(self.on_seq_changed)
        self.file_tree.selected.connect(self.on_file_selected)
        self.seq_combo.currentIndexChanged.connect(self.edit_data_frame)
        self.shot_combo.currentIndexChanged.connect(self.edit_data_frame)
        self.task_combo.currentIndexChanged.connect(self.edit_data_frame)
        self.tags_line_edit.textChanged.connect(self.edit_tags)
        self.source_widget.add_button.clicked.connect(self.on_source_add_clicked)
        self.source_widget.list.clicked.connect(self.on_source_selected)
        self.ingest_widget.list.clicked.connect(self.on_ingest_selected)
        self.ingest_widget.add_button.clicked.connect(self.on_add_ingest_event)
        self.publish_button.clicked.connect(self.publish_selected_asset)
        self.empty_state.files_added.connect(self.new_files_dragged)
        logging.info('Testing the popup')
        self.on_scope_changed()

    def on_source_add_clicked(self):
        print self.path_object.scope
        dialog = InputDialog(title='Add Source Company or Gear', message='Add an Import Source:', line_edit=True,
                             buttons=['Cancel', 'Add Source'])
        dialog.exec_()

        if dialog.button == 'Add Source':
            root_ = self.path_object.path_root.split(self.path_object.scope)[0]
            new_source = os.path.join(root_, 'IO', dialog.line_edit.text())
            if not os.path.exists(new_source):
                os.makedirs(new_source)
                self.parent().parent().centralWidget().update_location_to_latest(self.path_object)
            else:
                print 'Source %s already exists!' % new_source

    def file_interaction(self, files, path, to_folder):
        # TODO - ultimately we want to figure out how to handle the progress bar through the cgl_execute function.
        if path == '*':
            print 'Please Select An Ingest Source Before Dragging Files'
            return
        from core.utils.general import cgl_copy
        publish_data_csv = os.path.join(to_folder, 'publish_data.csv').replace('\\', '/')
        if os.path.exists(to_folder):
            create_new = False
        else:
            create_new = True
        cgl_copy(files, to_folder, verbose=False, dest_is_folder=True)
        self.progress_bar.hide()
        if create_new:
            self.load_import_events(new=True)
            num = self.ingest_widget.list.count()
            item = self.ingest_widget.list.item(num - 1)
            item.setSelected(True)
            self.parent().parent().centralWidget().update_location_to_latest(self.path_object)
            # self.empty_state.hide()
        if os.path.exists(publish_data_csv):
            os.remove(publish_data_csv)
            time.sleep(.5)  # seems like on the network i have to force it to sleep so it has time to delete.
        self.load_data_frame()
        self.populate_tree()

    def new_files_dragged(self, files):
        """
        What happens when i drag something to new files.
        :param files:
        :return:
        """
        to_folder = self.path_object.path_root
        path = self.path_object.ingest_source
        self.progress_bar.show()
        #QtWidgets.qApp.processEvents()
        file_process = threading.Thread(target=self.file_interaction, args=(files, path, to_folder))
        #QtWidgets.qApp.processEvents()
        file_process.start()

        # TODO - how do i know if the location changed?
        # if os.path.exists(to_folder):
        #     print 'dragging to exsting folder'
        # else:
        #     print 'dragging to new folder'
        #     self.location_changed.emit(self.path_object)
        # self.empty_state.hide()
        # TODO - No idea why none of these are working for selecting the version.
        # num = self.ingest_widget.list.count()
        # item = self.ingest_widget.list.item(num - 1)
        # item.setSelected(True)
        # self.ingest_widget.list.setCurrentItem(item)
        # self.ingest_widget.list.setCurrentRow(-1)

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

    def load_import_events(self, new=False):
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
        if not new:
            self.path_object = self.path_object.next_major_version()
        self.empty_state.setText('Drag Files Here to  %s' % self.path_object.version)

    def on_ingest_selected(self):
        self.ingest_widget.empty_state.hide()
        self.hide_tags()
        self.clear_all()
        self.path_object.set_attr(version=self.ingest_widget.list.selectedItems()[-1].text())
        # Load the Tree Widget
        self.load_data_frame()
        self.populate_tree()
        self.location_changed.emit(self.path_object)

    def populate_tree(self):
        self.file_tree.clear()
        if os.listdir(self.path_object.path_root):
            # self.empty_state.hide()
            self.version = self.path_object.version
            self.empty_state.setText('Drag Files To Add To Ingest %s' % self.version)
            self.file_tree.show()
            self.file_tree.directory = self.path_object.path_root
            self.file_tree.populate_from_data_frame(self.path_object, self.data_frame,
                                                    CONFIG['definitions']['ingest_browser_header'])
            self.tags_title.show()
            return
        else:
            self.file_tree.hide()
            self.hide_tags()
            self.empty_state.show()

    def load_data_frame(self):
        dir_ = self.path_object.path_root
        print 'loading %s' % dir_
        self.pandas_path = os.path.join(dir_, 'publish_data.csv')
        if os.path.exists(self.pandas_path):
            self.data_frame = pd.read_csv(self.pandas_path)
        else:
            data = []
            data = self.append_data_children(data, dir_)
            self.data_frame = pd.DataFrame(data, columns=CONFIG['definitions']['ingest_browser_header'])
        self.save_data_frame()

    def append_data_children(self, data, directory, parent='self'):
        # regex = r"#{3,}.[aA-zZ]{2,} \d{3,}-\d{3,}$"
        files = lj_list_dir(directory, basename=True)
        if files:
            for filename in files:
                type_ = get_file_type(filename)
                split_frange = split_sequence_frange(filename)
                if split_frange:
                    file_, frange = split_frange
                else:
                    file_ = filename
                    frange = ' '
                print file_
                print '\t', frange
                fullpath = os.path.join(os.path.abspath(directory), file_)
                data.append((file_, fullpath, type_, frange, ' ', False, ' ', ' ', ' ', ' ', ' ', ' ',
                             self.io_statuses[0], parent))
                if type_ == 'folder':
                    self.append_data_children(data, fullpath, file_)
            return data

    def save_data_frame(self):
        self.data_frame.to_csv(self.pandas_path, index=False)
        # can i set the value of the "Status" in the row?

    def edit_tags(self):
        files = self.current_selection
        tags = self.tags_line_edit.text()
        if tags:
            for f in files:
                row = self.data_frame.loc[self.data_frame['Filename'] == f[FILENAME]].index[0]
                self.data_frame.at[row, 'Tags'] = tags
            self.save_data_frame()

    def edit_data_frame(self):
        if self.current_selection[0][STATUS] == 'Published':
            return
        if self.seq_combo.currentText():
            seq = str(self.seq_combo.currentText())
            self.tags_title.setText('CGL:> Choose a %s Name or Type to Create a New One' %
                                    self.shot_label.text().title())
            if self.shot_combo.currentText():
                schema = CONFIG['project_management'][self.project_management]['tasks'][self.schema]
                if self.scope_combo.currentText():
                    proj_man_tasks = schema['long_to_short'][self.scope_combo.currentText()]
                else:
                    return
                shot = str(self.shot_combo.currentText())
                self.tags_title.setText('CGL:> Which Task will this be published to?')
                if self.task_combo.currentText():
                    try:
                        task = proj_man_tasks[str(self.task_combo.currentText())]
                        to_object = self.path_object.copy(scope=self.scope_combo.currentText(),
                                                          seq=seq,
                                                          shot=shot,
                                                          task=task,
                                                          context='render',
                                                          version='000.000',
                                                          user='publish',
                                                          resolution='high')
                        status = ''
                        for f in self.current_selection:
                            row = self.data_frame.loc[(self.data_frame['Filename'] == f[FILENAME]) &
                                                      (self.data_frame['Parent'] == f[PARENT])].index[0]
                            status = self.data_frame.at[row, 'Status']
                            if status == 'Imported':
                                status = 'Tagged'
                            to_path = os.path.join(to_object.path_root, f[FILENAME])
                            if status == 'Published':
                                self.tags_title.setText('CGL:>  Published!')
                                # self.tags_button.clicked.connect(lambda: self.go_to_location(to_path))
                                # self.tags_button.show()
                                # self.publish_button.hide()
                            else:
                                self.tags_title.setText('CGL:>  Tagged & Ready For Publish!')
                                self.publish_button.setEnabled(True)
                            self.data_frame.at[row, 'Scope'] = self.scope_combo.currentText()
                            self.data_frame.at[row, 'Seq'] = seq
                            self.data_frame.at[row, 'Shot'] = shot
                            self.data_frame.at[row, 'Task'] = task
                            self.data_frame.at[row, 'Publish_Filepath'] = to_path
                            self.data_frame.at[row, 'Status'] = status
                        for each in self.file_tree.selectionModel().selectedRows():
                            self.file_tree.set_text(each, PUBLISH_FILEPATH, to_path)
                            self.file_tree.set_text(each, STATUS, status)
                            self.file_tree.set_text(each, SCOPE, self.scope_combo.currentText())
                            self.file_tree.set_text(each, SEQ, seq)
                            self.file_tree.set_text(each, SHOT, shot)
                            self.file_tree.set_text(each, TASK, task)
                        self.save_data_frame()

                        # how do i edit the text only on the selected item?
                    except KeyError:
                        print 'Error with something:'
                        print 'scope', self.scope_combo.currentText()
                        print 'seq', seq
                        print 'shot', shot


    def go_to_location(self, to_path):
        path_object = PathObject(to_path).copy(context='source', user='', resolution='', filename='', ext='',
                                               filename_base='', version='')
        self.location_changed.emit(path_object)

    def clear_all(self):
        self.scope_combo.setCurrentIndex(0)
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
            f = data[0]
            try:
                row = self.data_frame.loc[(self.data_frame['Filename'] == f[FILENAME]) &
                                          (self.data_frame['Parent'] == f[PARENT])].index[0]
            except IndexError:
                self.hide_tags()
                return
            scope = self.data_frame.loc[row, 'Scope']
            seq = self.data_frame.loc[row, 'Seq']
            shot = self.data_frame.loc[row, 'Shot']
            task = self.data_frame.loc[row, 'Task']
            if type(scope) != float:
                if scope:
                    if scope != ' ':
                        self.set_combo_to_text(self.scope_combo, scope)
            if type(seq) != float:
                if seq:
                    if seq != ' ':
                        try:
                            seq = '%03d' % int(seq)
                            self.set_combo_to_text(self.seq_combo, seq)
                        except ValueError:
                            self.set_combo_to_text(self.seq_combo, seq)
            if type(shot) != float:
                if shot:
                    if shot != ' ':
                        try:
                            length = CONFIG['rules']['path_variables']['shot']['length']
                            if length == 3:
                                shot = '%03d' % int(shot)
                            elif length == 4:
                                shot = '%04d' % int(shot)
                            elif length == 5:
                                shot = '%05d' % int(shot)
                            self.set_combo_to_text(self.shot_combo, shot)
                        except ValueError:
                            self.set_combo_to_text(self.shot_combo, shot)
            if type(task) != float:
                if task:
                    if task != ' ':
                        task = self.schema_dict['short_to_long'][self.scope_combo.currentText()][task]
                        # task = self.proj_man_tasks_short_to_long[task]
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

    def show_tags_gui(self):
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

    def populate_tasks(self):
        self.task_combo.clear()
        ignore = ['default_steps', '']
        schema = CONFIG['project_management'][self.project_management]['tasks'][self.schema]
        tasks = schema['long_to_short'][self.scope_combo.currentText()]
        self.populate_seq()
        task_names = ['']
        for each in tasks:
            if each not in ignore:
                task_names.append(each)
        self.task_combo.addItems(sorted(task_names))

    def populate_seq(self):
        self.seq_combo.clear()
        self.seq_combo.lineEdit().setPlaceholderText('Type, or Choose')
        seqs = ['']
        if self.scope_combo.currentText() == 'shots':
            element = 'seq'
        else:
            element = 'type'
        if self.scope_combo.currentText() == 'shots':
            seqs = self.path_object.copy(seq='*', scope=self.scope_combo.currentText()).glob_project_element(element)
        elif self.scope_combo.currentText() == 'assets':
            seqs = CONFIG['asset_category_long_list']
        if not seqs:
            seqs = ['']
        self.seq_combo.addItems(seqs)
        return seqs

    def on_scope_changed(self):
        # see if we can set scope based off the data_frame
        if self.scope_combo.currentText():
            if self.scope_combo.currentText() == 'assets':
                self.seq_label.setText('Type')
                self.shot_label.setText('Asset')
            elif self.scope_combo.currentText() == 'shots':
                self.seq_label.setText('Sequence')
                self.shot_label.setText('Shot')
            self.tags_title.setText("<b>CGL:></b>  Type to Create a %s or Choose it from the list" %
                                    (self.seq_label.text()))
            self.populate_seq()
            self.populate_tasks()

    def on_seq_changed(self):
        shots = None
        self.shot_combo.clear()
        scope = self.scope_combo.currentText()
        seq = self.seq_combo.currentText()
        if seq:
            _ = self.path_object.copy(scope=scope, seq=seq, shot='*')
            if self.scope_combo.currentText() == 'shots':
                shots = self.path_object.copy(scope=scope, seq=seq, shot='*').glob_project_element('shot')
            elif self.scope_combo.currentText() == 'assets':
                shots = self.path_object.copy(scope=scope, seq=seq, shot='*').glob_project_element('asset')
            if shots:
                shots.insert(0, '')
                self.shot_combo.addItems(shots)

    def on_file_selected(self, data):
        self.tags_title.setText("<b>CGL:></b>  Choose 'Assets' or 'Shots' for your scope")
        print 'file selected, showing gui'
        self.show_tags_gui()
        self.current_selection = data
        self.scope_combo.setCurrentIndex(0)

        self.seq_combo.clear()
        self.shot_combo.clear()
        self.task_combo.clear()
        self.tags_line_edit.clear()
        self.sender().parent().show_combo_info(data)
        if not self.task_combo.currentText():
            self.publish_button.setEnabled(False)
        else:
            self.publish_button.setEnabled(True)
        if self.current_selection[0][STATUS] == "Published":
            self.view_in_lumbermill.show()
            self.hide_tags()
            self.publish_button.setEnabled(False)
        else:
            self.view_in_lumbermill.hide()
            self.show_tags_gui()
            self.publish_button.setEnabled(True)
        # self.sender().parent().show_tags_gui(files=files)
        # self.sender().parent().show_tags_info(data)

    def on_view_in_lumbermill_clicked(self):
        path_object = PathObject(self.current_selection[0][PUBLISH_FILEPATH]).copy(context='source',
                                                                                   user='',
                                                                                   resolution='',
                                                                                   filename='',
                                                                                   ext='',
                                                                                   filename_base='',
                                                                                   version='')
        self.location_changed.emit(path_object)

    def on_add_ingest_event(self):
        # deselect everything in the event
        # change the file path to reflect no selection
        self.path_object = self.path_object.next_major_version()
        self.empty_state.setText('Drag Media Here to  %s' % self.path_object.version)
        self.hide_tags()
        self.file_tree.hide()
        self.empty_state.show()

    def publish_selected_asset(self):
        task = self.schema_dict['long_to_short'][self.scope_combo.currentText()][self.task_combo.currentText()]
        # TODO - would be nice to figure out a more elegant way of doing this.  Perhaps handle the exception
        # within the Preflight itself?
        try:
            dialog = Preflight(self, software='ingest', preflight=task, data_frame=self.data_frame,
                               file_tree=self.file_tree, pandas_path=self.pandas_path,
                               current_selection=self.current_selection,
                               selected_rows=self.file_tree.selectionModel().selectedRows(),
                               ingest_browser_header=CONFIG['definitions']['ingest_browser_header'])
        except KeyError:
            dialog = Preflight(self, software='ingest', preflight='default', data_frame=self.data_frame,
                               file_tree=self.file_tree, pandas_path=self.pandas_path,
                               current_selection=self.current_selection,
                               selected_rows=self.file_tree.selectionModel().selectedRows(),
                               ingest_browser_header=CONFIG['definitions']['ingest_browser_header'])
        dialog.show()

    # noinspection PyListCreation
    @staticmethod
    def make_source_file(to_path, row):
        source_path = PathObject(to_path)
        source_path.set_attr(context='source')
        source_path.set_attr(filename='system_report.csv')
        dir_ = os.path.dirname(source_path.path_root)
        if not os.path.exists(dir_):
            os.makedirs(dir_)
        data = []
        data.append((row["Filepath"], row["Filename"], row["Filetype"], row["Frame_Range"], row["Tags"],
                     row["Keep_Client_Naming"], row["Scope"], row["Seq"], row["Shot"], row["Task"],
                     row["Publish_Filepath"], row["Publish_Date"], row["Status"]))
        df = pd.DataFrame(data, columns=CONFIG['definitions']['ingest_browser_header'])
        df.to_csv(source_path.path_root, index=False)

    def clear_layout(self, layout=None):
        clear_layout(self, layout)

    def sizeHint(self):
        return QtCore.QSize(self.height_hint, self.width_hint)

