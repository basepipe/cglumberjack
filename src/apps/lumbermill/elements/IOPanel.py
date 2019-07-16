import os
import shutil
import pandas as pd
import logging
import glob
import datetime
# noinspection PyUnresolvedReferences
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.dialog import InputDialog
from cglui.widgets.containers.tree import LJTreeWidget
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.widgets import LJListWidget, EmptyStateWidget
from cglcore.config import app_config
from cglcore.path import PathObject, CreateProductionData, icon_path, lj_list_dir, split_sequence_frange, get_file_type, split_sequence
from plugins.preflight.main import Preflight

FILEPATH = 0
FILENAME = 1
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
        self.project_management = app_config()['account_info']['project_management']
        if self.project_management == 'ftrack':
            self.schema = app_config()['project_management'][self.project_management]['api']['default_schema']
            self.schema_dict = app_config()['project_management'][self.project_management]['tasks'][self.schema]
        #self.tasks_dict = self.schema_dict['long_to_short'][self.scope_combo.currentText()]
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
        self.height_hint = 600
        self.current_selection = None

        self.path_object.set_attr(scope='IO')
        self.path_object.set_attr(ingest_source='*')
        self.data_frame = None
        self.pandas_path = ''
        self.io_statuses = ['Imported', 'Tagged', 'Published']

        self.file_tree = LJTreeWidget(self)
        self.width_hint = self.file_tree.width_hint

        pixmap = QtGui.QPixmap(icon_path('back24px.png'))
        import_empty_icon = QtGui.QIcon(pixmap)

        self.source_widget = LJListWidget('Sources', pixmap=None)
        self.ingest_widget = LJListWidget('Ingests', pixmap=None, empty_state_text='Select Source',
                                          empty_state_icon=import_empty_icon)
        #self.import_events.hide()f

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

        h_layout.addWidget(self.source_widget)
        h_layout.addWidget(self.ingest_widget)
        self.panel.addLayout(h_layout)
        self.panel.addWidget(self.empty_state)
        self.panel.addWidget(self.file_tree)

        self.panel.addLayout(self.tags_title_row)
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
        from cglui.progress_gif import ProgressDialog
        dialog = ProgressDialog()
        # dialog.show()gif doesn't show in this version
        dialog.exec_() # background doesn't run while this is going.
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
        dialog.accept()

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
        self.load_data_frame()
        self.populate_tree()
        self.location_changed.emit(self.path_object)

    def populate_tree(self):
        self.file_tree.clear()
        if os.listdir(self.path_object.path_root):
            self.empty_state.hide()
            self.file_tree.show()
            self.file_tree.directory = self.path_object.path_root
            self.file_tree.populate_from_data_frame(self.path_object, self.data_frame,
                                                    app_config()['definitions']['ingest_browser_header'])
            self.tags_title.show()
            return
        else:
            self.file_tree.hide()
            self.hide_tags()
            self.empty_state.show()

    def load_data_frame(self):
        dir_ = self.path_object.path_root
        self.pandas_path = os.path.join(dir_, 'publish_data.csv')
        if os.path.exists(self.pandas_path):
            self.data_frame = pd.read_csv(self.pandas_path)
        else:
            data = []
            for filename in lj_list_dir(dir_, basename=True):
                file_ = filename
                frange = ' '
                fullpath = os.path.join(os.path.abspath(dir_), filename)
                type_ = get_file_type(filename)
                if type_ == 'sequence':
                    file_, frange = split_sequence_frange(filename)
                data.append((fullpath, file_, type_, frange, ' ', False, ' ', ' ', ' ', ' ', ' ', ' ', self.io_statuses[0]))
            self.data_frame = pd.DataFrame(data, columns=app_config()['definitions']['ingest_browser_header'])
        self.save_data_frame()

    def save_data_frame(self):
        self.data_frame.to_csv(self.pandas_path, index=False)
        # can i set the value of the "Status" in the row?

    def edit_tags(self):
        files = self.current_selection
        tags = self.tags_line_edit.text()
        if tags:
            for f in files:
                row = self.data_frame.loc[self.data_frame['Filename'] == f[1]].index[0]
                self.data_frame.at[row, 'Tags'] = tags
            self.save_data_frame()

    def edit_data_frame(self):
        files = self.current_selection
        schema = app_config()['project_management'][self.project_management]['tasks'][self.schema]
        proj_man_tasks = schema['long_to_short'][self.scope_combo.currentText()]
        if self.seq_combo.currentText():
            seq = str(self.seq_combo.currentText())
            self.tags_title.setText('CGL:> Choose a %s Name or Type to Create a New One' % self.shot_label.text().title())
            if self.shot_combo.currentText():
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
                        for f in files:
                            row = self.data_frame.loc[self.data_frame['Filename'] == f[1]].index[0]
                            status = self.data_frame.at[row, 'Status']
                            if status == 'Imported':
                                status = 'Tagged'
                            to_path = os.path.join(to_object.path_root, f[1])
                            if status == 'Published':
                                self.tags_title.setText('CGL:>  Published!')
                                self.tags_button.clicked.connect(lambda: self.go_to_location(to_path))
                                self.tags_button.show()
                                # self.publish_button.hide()
                            else:
                                self.tags_title.setText('CGL:>  Tagged & Ready For Publish!')
                            self.data_frame.at[row, 'Scope'] = self.scope_combo.currentText()
                            self.data_frame.at[row, 'Seq'] = seq
                            self.data_frame.at[row, 'Shot'] = shot
                            self.data_frame.at[row, 'Task'] = task
                            self.data_frame.at[row, 'Publish_Filepath'] = to_path
                            self.data_frame.at[row, 'Status'] = status
                        for each in self.file_tree.selectionModel().selectedRows():
                            self.file_tree.model.item(each.row(), STATUS).setText(status)
                        self.save_data_frame()
                    except KeyError:
                        print 'Error with something:'
                        print 'scope', self.scope_combo.currentText()
                        print 'seq', seq
                        print 'shot', shot
        # UPDATE the tree with this info.

    def go_to_location(self, to_path):
        path_object = PathObject(to_path).copy(context='source', user='', resolution='', filename='', ext='', filename_base='', version='')
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
                row = self.data_frame.loc[self.data_frame['Filename'] == f[1]].index[0]
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
                            shot = '%04d' % int(shot)
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

    def show_tags_gui(self, files=None):
        if not files:
            files_text = 'files'
        else:
            if len(files) == 1:
                files_text = files[0]
            else:
                files_text = '%s files' % len(files)
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
        schema = app_config()['project_management'][self.project_management]['tasks'][self.schema]
        tasks = schema['long_to_short'][self.scope_combo.currentText()]
        seqs = self.populate_seq()
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
            seqs = app_config()['asset_category_long_list']
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
        else:
            print 'no scope chosen'

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
        self.show_tags_gui()
        self.current_selection = data
        self.scope_combo.setCurrentIndex(0)
        self.seq_combo.clear()
        self.shot_combo.clear()
        self.task_combo.clear()
        self.tags_line_edit.clear()
        self.sender().parent().show_combo_info(data)
        #self.sender().parent().show_tags_gui(files=files)
        #self.sender().parent().show_tags_info(data)

    def on_add_ingest_event(self):
        # deselect everything in the event
        # change the file path to reflect no selection
        self.hide_tags()
        self.file_tree.hide()
        self.empty_state.show()

    def publish_tagged_assets(self):
        # figure out what task we're publishing this thing to
        scope = self.scope_combo.currentText()
        task = self.schema_dict['long_to_short'][self.scope_combo.currentText()][self.task_combo.currentText()]
        #task = app_config()['pipeline_steps'][scope][self.task_combo.currentText()]
        try:
            this = Preflight(self, software='lumbermill', preflight=task, data_frame=self.data_frame,
                             file_tree=self.file_tree, pandas_path=self.pandas_path,
                             ingest_browser_header=app_config()['definitions']['ingest_browser_header'])
        except KeyError:
            this = Preflight(self, software='lumbermill', preflight='ingest_default', data_frame=self.data_frame,
                             file_tree=self.file_tree, pandas_path=self.pandas_path,
                             ingest_browser_header=app_config()['definitions']['ingest_browser_header'])
        this.exec_()
        return

    @staticmethod
    def make_source_file(to_path, row):
        source_path = PathObject(to_path)
        source_path.set_attr(context='source')
        source_path.set_attr(filename='system_report.csv')
        dir = os.path.dirname(source_path.path_root)
        if not os.path.exists(dir):
            os.makedirs(dir)
        data = []
        data.append((row["Filepath"], row["Filename"], row["Filetype"], row["Frame_Range"], row["Tags"],
                     row["Keep_Client_Naming"], row["Scope"], row["Seq"], row["Shot"], row["Task"],
                     row["Publish_Filepath"], row["Publish_Date"], row["Status"]))
        df = pd.DataFrame(data, columns=app_config()['definitions']['ingest_browser_header'])
        df.to_csv(source_path.path_root, index=False)

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def sizeHint(self):
        return QtCore.QSize(self.height_hint, self.width_hint)

