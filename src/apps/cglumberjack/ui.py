import glob
import copy
import os
from Qt import QtWidgets, QtCore, QtGui
from core.config import app_config
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJMainWindow
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from core.path import PathObject
from asset_ingestor_widget import AssetIngestor


class LabelEditRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.lineEdit = QtWidgets.QLineEdit()
        self.addWidget(self.label)
        self.addWidget(self.lineEdit)


class LabelComboRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('+')
        self.h_layout = QtWidgets.QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.add_button)
        self.combo = AdvComboBox()
        self.addLayout(self.h_layout)
        self.addWidget(self.combo)
        
    def hide(self):
        self.label.hide()
        self.combo.hide()
        
    def show(self):
        self.label.show()
        self.combo.show()


class FunctionButtons(QtWidgets.QHBoxLayout):
    def __init__(self):
        QtWidgets.QHBoxLayout.__init__(self)
        self.open_button = QtWidgets.QPushButton('Open')
        self.publish_button = QtWidgets.QPushButton('Publish')
        self.review_button = QtWidgets.QPushButton('Review')
        self.version_up = QtWidgets.QPushButton('Version Up')

        self.addWidget(self.open_button)
        self.addWidget(self.version_up)
        self.addWidget(self.review_button)
        self.addWidget(self.publish_button)


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)

        self.versions = AdvComboBox()
        self.versions.setMinimumWidth(500)
        self.versions.hide()

        self.users_label = QtWidgets.QLabel("  User:")
        self.users = AdvComboBox()
        self.users_layout = QtWidgets.QHBoxLayout(self)
        self.users_layout.addWidget(self.users_label)
        self.users_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.users_layout.addWidget(self.users)

        self.resolutions = AdvComboBox()
        self.resolutions_layout = QtWidgets.QHBoxLayout(self)
        self.resolutions_label = QtWidgets.QLabel("  Resolution:")
        self.resolutions_layout.addWidget(self.resolutions_label)
        self.resolutions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.resolutions_layout.addWidget(self.resolutions)

        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.show_button = QtWidgets.QToolButton()
        self.show_button.setText("more")
        self.hide_button = QtWidgets.QToolButton()
        self.hide_button.setText("less")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumHeight(200)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.versions)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.show_button)
        h_layout.addWidget(self.hide_button)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        self.hide_combos()

        self.message.hide()
        self.add_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        self.add_button.clicked.connect(self.on_add_button_clicked)
        
    def hide(self):
        self.hide_button.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.search_box.hide()
        self.show_button.hide()
        self.hide_button.hide()
        self.title.hide()
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()
        
    def show(self, combos=False):
        self.show_button.show()
        self.data_table.show()
        self.search_box.show()
        self.show_button.show()
        self.hide_button.show()
        self.title.show()
        if combos:
            self.show_combos()
            
    def show_combos(self):
        self.users.show()
        self.users_label.show()
        self.resolutions.show()
        self.resolutions_label.show()
        
    def hide_combos(self):
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()
        
    def hideall(self):
        self.hide_button.hide()
        self.data_table.hide()

    def showall(self):
        self.hide_button.show()
        self.show_button.hide()
        self.data_table.show()

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class CGLumberjackWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Environment Stuff
        self.path_object = None
        self.do_shotgun = False  # TODO - add this to the globals
        self.root = app_config()['paths']['root']
        self.company = app_config()['account_info']['company']
        self.context = 'source'
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        self.user = '*'
        self.user_default = app_config()['account_info']['user']
        self.version = ''
        self.task = ''
        self.resolution = ''
        self.current_location = {}
        layout = QtWidgets.QVBoxLayout(self)
        self.h_layout = QtWidgets.QHBoxLayout(self)

        # Create the Left Panel
        self.filter_layout = QtWidgets.QVBoxLayout(self)
        self.user_widget = LabelComboRow('User')
        self.user_widget.combo.addItem(self.user_default)
        # company
        self.company_widget = LabelComboRow('Company')
        # filters
        self.project_filter = AssetWidget(self, title="Project")
        self.project_filter.showall()
        self.project_filter.add_button.show()
        self.project_filter.hide_button.hide()
        self.radio_label = QtWidgets.QLabel('<b>Filter</b>')
        self.radio_layout = QtWidgets.QHBoxLayout(self)
        self.radio_user = QtWidgets.QRadioButton('User Assignments')
        self.radio_everyone = QtWidgets.QRadioButton('Everything')
        self.radio_publishes = QtWidgets.QRadioButton('Publishes')

        self.radio_layout.addWidget(self.radio_user)
        self.radio_user.setChecked(True)
        self.radio_layout.addWidget(self.radio_publishes)
        self.radio_layout.addWidget(self.radio_everyone)
        self.radio_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        # assemble the filter_panel
        self.filter_layout.addLayout(self.user_widget)
        self.filter_layout.addLayout(self.company_widget)
        self.filter_layout.addWidget(self.radio_label)
        self.filter_layout.addLayout(self.radio_layout)
        self.filter_layout.addWidget(self.project_filter)

        # Create the Middle Panel
        self.middle_layout = QtWidgets.QHBoxLayout()
        self.assets = None
        self.assets_filter_default = 'Everything'

        # Create the Right Panel

        # Create Empty layouts for tasks as well as renders.
        self.task_layout = QtWidgets.QVBoxLayout()
        self.render_layout = QtWidgets.QVBoxLayout()

        # create the current path
        self.current_location_label = QtWidgets.QLabel('Current Location')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        self.cl_row = QtWidgets.QHBoxLayout()
        self.cl_row.addWidget(self.current_location_label)
        self.cl_row.addWidget(self.current_location_line_edit)

        # assemble the main h layout
        self.h_layout.addLayout(self.filter_layout)
        self.h_layout.addLayout(self.middle_layout)
        self.h_layout.addLayout(self.task_layout)
        self.h_layout.addLayout(self.render_layout)
        self.h_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                    QtWidgets.QSizePolicy.Minimum))
        layout.addLayout(self.cl_row)
        layout.addLayout(self.h_layout)

        self.load_companies()
        self.load_projects()

        self.project_filter.data_table.selected.connect(self.on_project_changed)

    def load_companies(self, company=None):
        self.company_widget.combo.clear()
        companies = glob.glob('%s/*' % self.root)
        self.company_widget.combo.addItem('')
        for each in companies:
            c = os.path.split(each)[-1]
            if 'cgl-' in c:
                self.company_widget.combo.addItem(c)
        if not company:
            company = self.company
        index = self.company_widget.combo.findText(company)
        if index:
            self.company_widget.combo.setCurrentIndex(index)

    def load_projects(self):
        d = {'root': self.root,
             'company': self.company,
             'project': 'filler',
             'scope': 'source'}
        obj = PathObject(d)
        print obj.path_root
        return
        projects = obj.glob_project_element('project')
        if not projects:
            print 'no projects'
            self.project_filter.search_box.setEnabled(False)
            self.project_filter.data_table.setEnabled(False)
            self.radio_user.setEnabled(False)
            self.radio_everyone.setEnabled(False)
            self.radio_publishes.setEnabled(False)
            self.radio_label.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.search_box.setEnabled(True)
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('+')
            self.radio_user.setEnabled(True)
            self.radio_everyone.setEnabled(True)
            self.radio_publishes.setEnabled(True)
            self.radio_label.setEnabled(True)
        self.project_filter.setup(ListItemModel(self.prep_list_for_table(projects, path_filter=None), ['Name']))
        self.update_location()

    def load_assets(self):
        print self.path_object.path_root
        data = []
        items = glob.glob(self.path_object.path_root)
        temp_ = []
        for each in items:
            print each
            each_obj = PathObject(each)
            #print each_obj.path_root
            #print each_obj.shotname
            return
            if each_obj.shotname not in temp_:
                temp_.append(each_obj.shotname)
                data.append([each_obj.shotname, each, ''])
        self.assets.setup(ListItemModel(data, ['Name', 'Path', 'Due Date']))
        self.assets.data_table.hideColumn(1)
        self.assets.data_table.set_draggable(True)
        #self.assets.data_table.dropped.connect(self.on_file_dragged_to_assets)
        #self.assets.add_button.clicked.connect(self.on_create_asset)

    # METHODS FOR WHEN USERS CLICK THINGS

    def on_assets_filter_changed(self):
        filter_ = self.assets.resolutions.currentText()
        self.assets_filter_default = filter_
        self.version = ''
        self.resolution = ''
        self.current_location['task'] = '*'
        self.seq = '*'
        self.shot = '*'
        self.task = '*'
        self.user = filter_
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        self.update_location()
        self.load_assets()

    def on_project_changed(self, data):
        self.project = data[0][0]
        # reset the env vars after a project change
        self.seq = '*'
        self.shot = '*'
        self.resolution = ''
        self.version = ''
        self.task = '*'
        # build the asset Widget
        self.clear_layout(self.middle_layout)
        self.assets = AssetWidget(self, title="")
        self.assets.set_title('Project: %s' % self.project)
        self.assets.add_button.show()
        self.radio_publishes.clicked.connect(self.on_assets_filter_changed)

        # update location and display the resulting assets.
        self.update_location()
        self.assets.showall()
        self.assets.hide_button.hide()
        self.middle_layout.addWidget(self.assets)

        self.load_assets()
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        self.assets.data_table.selected.connect(self.on_main_asset_selected)
        self.radio_publishes.show()
        self.radio_everyone.show()
        self.radio_user.show()
        self.radio_everyone.toggled.connect(self.on_assets_filter_changed)
        self.radio_publishes.toggled.connect(self.on_assets_filter_changed)
        self.radio_user.toggled.connect(self.on_assets_filter_changed)

    def on_main_asset_selected(self, data):
        # data format: ['Project', 'Seq', 'Shot', 'Task', 'User', 'Path']
        print data
        return
        if data:
            path = data[0][1]
            self.user = ''
            self.version = ''
            self.resolution = ''
            self.current_location = PathParser.dict_from_path(path)
            self.current_location['task'] = '*'
            current_path = PathParser.path_from_dict(self.current_location, with_root=True)
            tasks = glob.glob(current_path)
            task_list = []
            for each in tasks:
                d = PathParser.dict_from_path(each)
                self.shot = d['shot']
                self.seq = d['seq']
                if self.project == '*':
                    self.project = d['project']
                task_list = self.append_unique_to_list(d['task'], task_list)
            self.task_layout.tasks = []
            self.clear_layout(self.task_layout)
            self.clear_layout(self.render_layout)

            # this should possibly be its own method (load_tasks) or something like that.
            task_label = QtWidgets.QLabel('<b>Tasks</b>')
            task_add = QtWidgets.QToolButton()
            task_add.setText('+')
            task_label_layout = QtWidgets.QHBoxLayout()
            task_label_layout.addWidget(task_label)
            task_label_layout.addWidget(task_add)
            task_label_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                            QtWidgets.QSizePolicy.Minimum))

            self.task_layout.addLayout(task_label_layout)
            self.update_location()
            for each in task_list:
                if each not in self.task_layout.tasks:
                    version_location = copy.copy(self.current_location)
                    task_widget = AssetWidget(self, each)
                    task_widget.data_table.selected.connect(self.on_task_selected)
                    task_widget.versions.currentIndexChanged.connect(self.on_task_version_changed)
                    task_widget.users.currentIndexChanged.connect(self.on_task_user_changed)
                    task_widget.resolutions.currentIndexChanged.connect(self.on_task_resolution_changed)
                    task_widget.showall()
                    task_widget.search_box.hide()
                    task_widget.hide_button.hide()
                    task_widget.show_button.show()
                    # populate this bitch
                    version_location['task'] = each
                    version_location['user'] = self.populate_users_combo(task_widget, each)
                    version_location['version'] = self.populate_versions_combo(task_widget.users,
                                                                               task_widget.versions,
                                                                               each)
                    version_location['resolution'] = self.populate_resolutions_combo(task_widget.users,
                                                                                     task_widget.versions,
                                                                                     task_widget.resolutions,
                                                                                     each)
                    version_location['filename'] = '*'
                    task_widget.data_table.task = each
                    task_widget.data_table.user = version_location['user']
                    task_widget.data_table.version = version_location['version']
                    task_widget.data_table.resolution = version_location['resolution']
                    version_path = PathParser.path_from_dict(version_location, with_root=True)
                    files_ = glob.glob(version_path)
                    task_widget.setup(ListItemModel(self.prep_list_for_table(files_, split_for_file=True), ['Name']))
                    self.task_layout.addWidget(task_widget)
                    self.task_layout.tasks.append(each)
                    self.task_layout.addItem((QtWidgets.QSpacerItem(22, 0, QtWidgets.QSizePolicy.Expanding,
                                              QtWidgets.QSizePolicy.Minimum)))

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def update_location(self):
        self.current_location = {'company': self.company, 'root': self.root, 'scope': self.scope,
                                 'context': self.context, 'project': self.project, 'seq': self.seq, 'shot': self.shot,
                                 'user': self.user, 'version': self.version, 'task': self.task,
                                 'resolution': self.resolution
                                 }
        self.path_object = PathObject(self.current_location)
        self.current_location_line_edit.setText(self.path_object.path_root)

    @staticmethod
    def append_unique_to_list(item, item_list):
        if item not in item_list:
            item_list.append(item)
        return item_list

    @staticmethod
    def prep_list_for_table(list_, path_filter=None, split_for_file=False):
        # TODO - would be awesome to make this smart enough to know what to do with a dict, list, etc...
        # TODO - this could be a little clearer on what it's meant to be doing.
        list_.sort()
        output_ = []
        for each in list_:
            if path_filter:
                obj = PathObject(each)
                output_.append([obj.data[path_filter]])
            else:
                if split_for_file:
                    each = os.path.split(each)[-1]
                output_.append([each])
        return output_


class CGLumberjack(LJMainWindow):
    def __init__(self):
        LJMainWindow.__init__(self)
        self.setCentralWidget(CGLumberjackWidget(self))
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        menu_bar = self.menuBar()
        icon = QtGui.QPixmap(":images/'lumberjack.24px.png").scaled(24, 24)
        self.setWindowIcon(icon)
        tools_menu = menu_bar.addMenu('&Tools')
        settings = QtWidgets.QAction('Settings', self)
        settings.setShortcut('Ctrl+,')
        shelves = QtWidgets.QAction('Shelf Builder', self)
        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(shelves)
        # connect signals and slots
        settings.triggered.connect(self.on_settings_clicked)
        shelves.triggered.connect(self.on_shelves_clicked)

    def on_settings_clicked(self):
        from apps.configurator.main import Configurator
        dialog = Configurator(self)
        dialog.exec_()

    def on_shelves_clicked(self):
        from apps.shelf_tool.main import ShelfTool
        dialog = ShelfTool(self)
        dialog.exec_()





if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = CGLumberjack()
    td.setWindowTitle('CG Lumberjack')
    td.show()
    td.raise_()
    app.exec_()
