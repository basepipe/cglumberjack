import getpass
import os
import json
import time
import requests
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.utils import read_write, web
import plugins.syncthing.utils as syncthing



DEFAULT_ROOT = r"C:\CGLUMBERJACK\COMPANIES"
DEFAULT_CODE_ROOT = os.path.join(os.path.expanduser("~"), 'PycharmProjects', 'cglumberjack')
DEFAULT_HOME = os.path.join(os.path.expanduser("~"), 'Documents', 'cglumberjack')
DEFAULT_USER_GLOBALS = os.path.join(DEFAULT_HOME, 'user_globals.json')
DEFAULT_GLOBALS = os.path.join(DEFAULT_ROOT, '_config', 'globals.json')


class PathItemWidget(QtWidgets.QWidget):
    line_edit_changed = QtCore.Signal(object)
    root_set = QtCore.Signal()

    def __init__(self, parent=None, paths_dict=None, hide_on_find=False):
        QtWidgets.QWidget.__init__(self, parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.globals_layout = QtWidgets.QGridLayout()
        self.paths_layout = QtWidgets.QGridLayout()
        self.vfx_paths_layout = QtWidgets.QGridLayout()
        self.user_dir = os.path.expanduser("~")
        self.user_name = self.get_user_name()
        self.cgl_dir = self.get_default_cgl_dir()
        self.user_globals_path = self.get_user_config(self.cgl_dir)
        self.globals_label = QtWidgets.QLabel('Globals Locations')
        self.globals_label.setProperty('class', 'ultra_title')
        self.paths_label = QtWidgets.QLabel('CGL Tool Paths')
        self.paths_label.setProperty('class', 'ultra_title')
        self.paths_label.hide()
        self.vfx_label = QtWidgets.QLabel('VFX Paths')
        self.vfx_label.setProperty('class', 'ultra_title')
        self.vfx_label.hide()
        # self.red_palette, self.green_palette, self.black_palette = define_palettes()
        self.cgl_tools_folder = None
        self.widget_dict = {}
        # Add User Globals, Root and The "Paths" label to the first slots.
        i = 0
        i = self.add_path_line(self.globals_layout, 'root', paths_dict, i, hide_on_find)
        self.add_path_line(self.globals_layout, 'user_globals', paths_dict, i, hide_on_find)

        self.layout.addWidget(self.paths_label)
        self.layout.addLayout(self.globals_layout)
        self.layout.addWidget(self.paths_label)
        self.layout.addLayout(self.paths_layout)
        self.layout.addWidget(self.vfx_label)
        self.layout.addLayout(self.vfx_paths_layout)

        default_paths = ['cgl_tools', 'code_root', 'dev_pkg', 'ffmpeg', 'ffplay', 'ffprobe',
                         'magick', 'wget', 'globals']
        vfx_paths = ['ari_convert', 'maketx', 'mayapy', 'nuke']
        prow = 0
        vrow = 0

        for key in paths_dict:
            if key in default_paths:
                prow += 2
                self.add_path_line(self.paths_layout, key, paths_dict, prow, hide_on_find)
            elif key in vfx_paths:
                vrow += 2
                self.add_path_line(self.vfx_paths_layout, key, paths_dict, vrow, hide_on_find)

    def add_path_line(self, layout_, key, paths_dict, row, hide_on_find):
        """

        :param layout_:
        :param key:
        :param paths_dict:
        :param row:
        :param hide_on_find:
        :return:
        """
        label = QtWidgets.QLabel(key)
        line_edit = QtWidgets.QLineEdit()

        line_edit.setText(paths_dict[key])
        if key == 'root':
            line_edit.editingFinished.connect(self.on_root_set)

        folder_button = QtWidgets.QToolButton()
        if key == 'cgl_tools':
            self.cgl_tools_folder = folder_button
        folder_button.setIcon(QtGui.QIcon(self.icon_path('folder24px.png')))
        folder_button.line_edit = line_edit
        folder_button.label = label
        message = QtWidgets.QLabel('Path Not Found, Please Specify %s' % key)
        # message.setPalette(self.red_palette)
        folder_button.message = message
        self.widget_dict[key] = {'label': label,
                                 'line_edit': line_edit,
                                 'message': message}
        layout_.addWidget(label, row, 0)
        layout_.addWidget(line_edit, row, 1)
        layout_.addWidget(folder_button, row, 2)
        layout_.addWidget(message, row + 1, 1)
        folder_button.clicked.connect(self.on_path_chosen)
        self.check_path(key, label, line_edit, message, folder_button, hide_on_find=hide_on_find)
        line_edit.textChanged.connect(lambda: self.on_line_edit_changed(key))
        return row+2

    def on_root_set(self):
        self.root_set.emit()


    @staticmethod
    def icon_path(filename):
        this = __file__.split('cglumberjack')[0]
        return os.path.join(this, 'cglumberjack', 'resources', 'icons', filename)

    def on_line_edit_changed(self, key):
        self.line_edit_changed.emit({key: self.sender()})

    def check_path(self, path_name, label, line_edit, message, folder_button, hide_on_find):
        path_ = line_edit.text()
        if os.path.exists(path_):
            line_edit.setEnabled(False)
            message.setText('%s Found Path, Ready for Ass Kicking!' % path_name)
            # message.setPalette(self.black_palette)
            self.hide_line(label, line_edit, message, folder_button, hide_on_find)
        else:
            if path_name == 'cgl_tools':
                line_edit.setEnabled(False)
                message.setText('%s Path Not Found, set "root"!' % path_name)
                self.hide_line(label, line_edit, message, folder_button, hide_on_find)
            elif path_name == 'code_root':
                code_root = __file__.split('cglumberjack')[0]
                code_root = '%s/cglumberjack' % code_root
                line_edit.setEnabled(False)
                line_edit.setText(code_root)
                message.setText('%s Path Found, Ready for Ass Kicking!' % path_name)
                # message.setPalette(self.black_palette)
                self.hide_line(label, line_edit, message, folder_button, hide_on_find)
            elif path_name == 'user_globals':
                line_edit.setText(self.user_globals_path)
                line_edit.setEnabled(False)
                message.setText('Setting As Default Location, Click Folder Button to Change')
                # message.setPalette(self.black_palette)
            elif path_name == 'globals':
                line_edit.setEnabled(False)
                message.setText('%s Path Not Found, set "root"!' % path_name)
                self.hide_line(label, line_edit, message, folder_button, hide_on_find, force_hide=False)

    @staticmethod
    def hide_line(label, line_edit, message, folder_button, hide_on_find, force_hide=False):
        if hide_on_find or force_hide:
            label.hide()
            line_edit.hide()
            message.hide()
            folder_button.hide()

    def on_path_chosen(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory()
        self.sender().line_edit.setText(folder)
        self.check_path(folder, self.sender().label, self.sender().line_edit, self.sender().message, self.sender(),
                        hide_on_find=True)
        if self.sender().label.text() == 'root':
            self.cgl_tools_folder.line_edit.setText(os.path.join(folder, '_config', 'cgl_tools'))
            self.cgl_tools_folder.message.setText('%s Path Found, Ready for Ass Kicking!' % 'cgl_tools')
            # self.cgl_tools_folder.message.setPalette(self.black_palette)

            self.widget_dict['globals']['line_edit'].setText(os.path.join(folder, '_config', 'globals.json'))
            self.widget_dict['globals']['message'].setText('%s Path Found, Ready for Ass Kicking!' % 'globals')
            # self.widget_dict['globals']['message'].setPalette(self.black_palette)

    @staticmethod
    def get_user_name():
        """
            find the currently logged in user
            Returns:
                str: username

        """
        return getpass.getuser()

    def get_default_cgl_dir(self):
        if 'Documents' in self.user_dir:
            cg_lumberjack_dir = os.path.join(self.user_dir, 'cglumberjack')
        else:
            cg_lumberjack_dir = os.path.join(self.user_dir, 'Documents', 'cglumberjack')
        return cg_lumberjack_dir

    @staticmethod
    def get_user_config(cgl_dir):
        return os.path.join(cgl_dir, 'user_globals.json')


class ConfigDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, company='', config_dict=None, root=r"C:\CGLUMBERJACK\COMPANIES"):
        QtWidgets.QDialog.__init__(self, parent)
        self.app_config = config_dict
        globals_path = os.path.join(root, '_config', 'config.json')
        self.proj_management_label = QtWidgets.QLabel('Project Management')
        self.contents = {}
        self.company = company
        self.global_config = {}
        self.root = root
        self.user_name = self.get_user_name()
        self.api_key = ''
        self.api_script = ''
        self.api_user = ''
        self.project_management = ''
        self.api_server = ''
        self.setWindowTitle('Create Globals')

        layout = QtWidgets.QVBoxLayout(self)
        self.project_management_label = QtWidgets.QLabel('Project Management:')
        self.project_management_label.setProperty('class', 'ultra_title')
        self.proj_management_label = QtWidgets.QLabel('Software:')
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['lumbermill', 'ftrack', 'shotgun'])
        # self.red_palette, self.green_palette, self.black_palette = define_palettes()

        self.user_email_label = QtWidgets.QLabel('User Email:')
        self.user_email_line_edit = QtWidgets.QLineEdit()
        self.user_name_label = QtWidgets.QLabel('User Name:')
        self.user_name_line_edit = QtWidgets.QLineEdit()
        self.user_name_line_edit.setText(self.user_name)
        self.globals_label = QtWidgets.QLabel('Globals')
        self.globals_label.setProperty('class', 'ultra_title')
        self.paths_label = QtWidgets.QLabel('Paths')
        self.paths_label.setProperty('class', 'ultra_title')

        self.server_label = QtWidgets.QLabel('server url:')
        self.api_key_label = QtWidgets.QLabel('api key:')
        self.api_user_label = QtWidgets.QLabel('api user:')
        self.api_script_label = QtWidgets.QLabel('api script:')
        self.root_label = QtWidgets.QLabel('Production Root:')
        self.server_line_edit = QtWidgets.QLineEdit()
        self.api_key_line_edit = QtWidgets.QLineEdit()
        self.api_user_line_edit = QtWidgets.QLineEdit()
        self.api_script_line_edit = QtWidgets.QLineEdit()

        self.choose_folder_button = QtWidgets.QToolButton()
        self.choose_folder_button.setText('...')
        self.choose_root = QtWidgets.QToolButton()
        self.choose_root.setText('...')
        self.choose_code_root_button = QtWidgets.QToolButton()
        self.choose_code_root_button.setText('...')

        self.proj_man_grid = QtWidgets.QGridLayout()
        self.proj_man_grid.addWidget(self.proj_management_label, 0, 0)
        self.proj_man_grid.addWidget(self.proj_management_combo, 0, 1)
        self.proj_man_grid.addWidget(self.api_key_label, 1, 0)
        self.proj_man_grid.addWidget(self.api_key_line_edit, 1, 1)
        self.proj_man_grid.addWidget(self.api_user_label, 2, 0)
        self.proj_man_grid.addWidget(self.api_user_line_edit, 2, 1)
        self.proj_man_grid.addWidget(self.server_label, 3, 0)
        self.proj_man_grid.addWidget(self.server_line_edit, 3, 1)
        self.proj_man_grid.addWidget(self.api_script_label, 4, 0)
        self.proj_man_grid.addWidget(self.api_script_line_edit, 4, 1)
        self.proj_man_grid.addWidget(self.user_name_label, 5, 0)
        self.proj_man_grid.addWidget(self.user_name_line_edit, 5, 1)
        self.proj_man_grid.addWidget(self.user_email_label, 6, 0)
        self.proj_man_grid.addWidget(self.user_email_line_edit, 6, 1)

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.button = ''
        self.ok_button.setEnabled(False)
        self.create_globals_button = QtWidgets.QPushButton('Create Globals')
        self.create_globals_button.setEnabled(False)

        # self.project_management = self.app_config['account_info']['project_management']

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.create_globals_button)
        button_layout.addWidget(self.ok_button)

        # self.globals_tree_widget = DictionaryTreeWidget({})
        this = __file__.split('cglumberjack')[0]
        this = __file__.split('cglumberjack')[0]
        dict_ = read_write.load_json(os.path.join(this, 'cglumberjack', 'cgl', 'cfg', 'globals_template.json'))
        self.proj_man_dict = dict_['project_management']
        self.path_item_widget = PathItemWidget(paths_dict=dict_['paths'], hide_on_find=True)

        if self.path_item_widget.widget_dict['root']['line_edit'].text():
            self.show_project_management_basics()
        else:
            self.hide_project_management_basics()
        self.widget_dict = self.path_item_widget.widget_dict

        layout.addWidget(self.globals_label)
        layout.addWidget(self.path_item_widget)
        layout.addWidget(self.project_management_label)
        layout.addLayout(self.proj_man_grid)
        # layout.addWidget(self.globals_tree_widget)
        # layout.addWidget(QHLine())
        layout.addLayout(button_layout)
        layout.addStretch(1)

        # self.user_globals_line_edit.setEnabled(False)
        self.proj_management_combo.currentIndexChanged.connect(self.on_pm_changed)
        self.path_item_widget.line_edit_changed.connect(self.on_line_edits_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.ok_button.hide()
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.create_globals_button.clicked.connect(self.on_create_globals_clicked)
        self.path_item_widget.root_set.connect(self.on_root_line_edit_set)
        self.user_email_line_edit.textChanged.connect(self.check_ok_to_create_globals)
        self.user_name_line_edit.textChanged.connect(self.check_ok_to_create_globals)
        self.proj_management_combo.currentIndexChanged.connect(self.check_ok_to_create_globals)
        self.get_input()

        self.hide_api_info()
        self.set_proj_man()
        self.check_user_config()
        # self.globals_tree_widget.hide()
        self.on_globals_changed()
        self.set_some_stuff()

    def check_ok_to_create_globals(self):
        not_ready = 0
        not_ready += self.widget_not_ready(self.proj_management_combo)
        not_ready += self.widget_not_ready(self.user_email_line_edit)
        not_ready += self.widget_not_ready(self.user_name_line_edit)
        if not_ready:
            self.create_globals_button.setEnabled(False)
        else:
            self.create_globals_button.setEnabled(True)
            self.create_globals_button.setAutoDefault(True)
            self.create_globals_button.setDefault(True)

    @staticmethod
    def widget_not_ready(widget):
        if isinstance(widget, QtWidgets.QLineEdit):
            text = widget.text()
            if text:
                return int(0)
            else:
                return int(1)
        elif isinstance(widget, QtWidgets.QComboBox):
            text = widget.currentText()
            if text:
                return int(0)
            else:
                return 1

    def set_some_stuff(self):
        root = self.widget_dict['root']['line_edit'].text()
        if root:
            self.widget_dict['cgl_tools']['line_edit'].setText(os.path.join(root, '_config', 'cgl_tools'))
            self.widget_dict['globals']['line_edit'].setText(os.path.join(root, '_config', 'globals.json'))
        # self.widget_dict['cgl_tools']['line_edit'].setText('test')

    def on_root_line_edit_set(self):
        self.show_project_management_basics()
        # change the lineEdit for cgl_tools


    @staticmethod
    def get_user_name():
        """
            find the currently logged in user
            Returns:
                str: username

        """
        return getpass.getuser()

    @staticmethod
    def on_line_edits_changed(data):
        print data

    def on_globals_changed(self):
        config = self.widget_dict['globals']['line_edit'].text()
        if os.path.exists(config):
            self.globals_message.hide()
            self.global_config = self.load_globals()
        else:
            self.global_config = self.load_globals_template()

    def on_user_config_changed(self):
        config = self.user_globals_line_edit.text()
        if os.path.exists(config):
            self.user_config_message.hide()

    def on_create_globals_clicked(self):
        self.create_global_config()
        self.create_user_globals()
        self.copy_cgl_tools()
        if self.project_management == 'ftrack':
            if not self.inherited_globals:
                import plugins.project_management.ftrack.setup_tasks as setup_tasks
                form_ = setup_tasks.TaskSetupGUI()
                form_.exec_()
        self.accept()

    def copy_cgl_tools(self):
        from cgl.core.utils.general import cgl_copy
        src = os.path.join(self.widget_dict['code_root']['line_edit'].text(), 'cgl', 'cfg', 'cgl_tools')
        dst = os.path.join(self.widget_dict['cgl_tools']['line_edit'].text())
        if not os.path.exists(dst):
            cgl_copy(src, dst)

    def create_global_config(self):
        if self.global_config:
            pm_dict = self.global_config['project_management'][self.proj_management_combo.currentText()]
            self.global_config['paths']['root'] = self.widget_dict['root']['line_edit'].text()
            self.global_config['paths']['cgl_tools'] = self.widget_dict['cgl_tools']['line_edit'].text()
            self.global_config['paths']['code_root'] = self.widget_dict['code_root']['line_edit'].text()
            self.global_config['account_info']['project_management'] = self.project_management
            self.global_config['account_info']['globals_path'] = self.widget_dict['globals']['line_edit'].text()
            self.global_config['paths']['user_globals'] = self.widget_dict['user_globals']['line_edit'].text()
            pm_dict['users'] = {self.user_name_line_edit.text(): {'email': self.user_email_line_edit.text(),
                                                                  'first': '',
                                                                  'last': '',
                                                                  'login': self.user_name_line_edit.text()}}
            api = self.global_config['project_management'][self.project_management]['api']
            if self.project_management == 'ftrack':
                api['api_key'] = self.api_key_line_edit.text()
                api['server_url'] = self.server_line_edit.text()
                api['api_user'] = self.api_user_line_edit.text()
                api['default_schema'] = 'VFX'
            elif self.project_management == 'shotgun':
                api['api_key'] = self.api_key_line_edit.text()
                api['server_url'] = self.server_line_edit.text()
                api['api_user'] = self.api_user_line_edit.text()
                api['api_script'] = self.api_script_line_edit.text()
            if not os.path.exists(os.path.dirname(self.widget_dict['root']['line_edit'].text())):
                os.makedirs(os.path.dirname(self.widget_dict['root']['line_edit'].text()))
            if not os.path.exists(os.path.dirname(self.widget_dict['globals']['line_edit'].text())):
                os.makedirs(os.path.dirname(self.widget_dict['globals']['line_edit'].text()))
            read_write.save_json(self.widget_dict['globals']['line_edit'].text(), self.global_config)
        else:
            print 'No Dictionary Loaded for Global Config'

    def check_user_config_exists(self):
        config = self.user_globals_line_edit.text()
        if os.path.exists(config):
            self.user_config_message.hide()
            self.create_user_config_button.hide()

    def create_user_globals(self):
        user_globals = self.widget_dict['user_globals']['line_edit'].text()
        if user_globals:
            if not os.path.exists(os.path.dirname(user_globals)):
                os.makedirs(os.path.dirname(user_globals))
            d = {
                 "globals": self.widget_dict['globals']['line_edit'].text(),
                 "previous_path": "",
                 "previous_paths": {},
                 "user_email": self.user_email_line_edit.text(),
                 "user_name": self.user_name_line_edit.text(),
                 "proj_man_user_email": self.api_user_line_edit.text(),
                 "proj_man_user_name": "",
                 "methodology": "local",
                 "my_tasks": {}
                 }
            read_write.save_json(user_globals, d)
        else:
            print 'No Root Defined, cannot save user globals'

    def load_user_config(self):
        pass

    def load_globals(self):
        globals_line_edit = self.widget_dict['globals']['line_edit']
        if globals_line_edit.text():
            globals_ = globals_line_edit.text()
            self.global_config = read_write.load_json(globals_)
            # self.globals_tree_widget.load_dictionary(self.global_config)
            # self.globals_tree_widget.show()
        return self.global_config

    def load_globals_template(self):
        code_root_line_edit = self.widget_dict['code_root']['line_edit']
        if code_root_line_edit.text():
            globals_ = os.path.join(code_root_line_edit.text(), 'cgl', 'cfg', 'globals_template.json')
            self.global_config = read_write.load_json(globals_)
            # elf.globals_tree_widget.load_dictionary(self.global_config)
            # self.globals_tree_widget.show()
            return self.global_config
        else:
            print 'Code Root Not Defined'
            return None

    def check_user_config(self):
        pass

    def cancel_clicked(self):
        self.accept()

    def show_project_management_basics(self):
        self.project_management_label.show()
        self.proj_management_label.show()
        self.proj_management_combo.show()
        self.user_email_label.show()
        self.user_email_line_edit.show()
        self.user_name_label.show()
        self.user_name_line_edit.show()

    def hide_project_management_basics(self):
        self.project_management_label.hide()
        self.proj_management_label.hide()
        self.proj_management_combo.hide()
        self.user_email_label.hide()
        self.user_email_line_edit.hide()
        self.user_name_label.hide()
        self.user_name_line_edit.hide()

    def hide_api_info(self):
        self.server_label.hide()
        self.api_key_label.hide()
        self.api_user_label.hide()
        self.server_line_edit.hide()
        self.api_key_line_edit.hide()
        self.api_user_line_edit.hide()
        self.api_script_label.hide()
        self.api_script_line_edit.hide()

    def show_api_info(self):
        self.server_label.show()
        self.api_key_label.show()
        self.api_user_label.show()
        self.server_line_edit.show()
        self.api_key_line_edit.show()
        self.api_user_line_edit.show()

    def set_proj_man(self):
        for software in self.proj_man_dict.keys():
            print software
            print self.proj_man_dict[software]['api']
            try:
                if self.proj_man_dict[software]['api']['server_url']:
                    print 'setting project management to %s' % software
                    index = self.proj_management_combo.findText(software)
                    if index != -1:
                        self.proj_management_combo.setCurrentIndex(index)
                        self.on_pm_changed()
            except KeyError:
                pass

    def on_pm_changed(self):
        self.project_management = self.proj_management_combo.currentText()
        api_key = self.proj_man_dict[self.project_management]['api']['api_key']
        api_user = self.proj_man_dict[self.project_management]['api']['api_user']
        server_url = self.proj_man_dict[self.project_management]['api']['server_url']
        try:
            api_script = self.proj_man_dict[self.project_management]['api']['api_script']
            self.api_script_line_edit.setText(api_script)
        except KeyError:
            print('No Api script found, skipping')
            self.api_script_line_edit.setText('')
        self.api_key_line_edit.setText(api_key)
        self.api_user_line_edit.setText(api_user)
        self.server_line_edit.setText(server_url)
        if self.project_management == 'lumbermill':
            self.hide_api_info()
        elif self.project_management == 'ftrack':
            self.show_api_info()
        elif self.project_management == 'shotgun':
            self.show_api_info()
            self.api_script_label.show()
            self.api_script_line_edit.show()
        elif self.project_management == '':
            self.hide_api_info()
        self.get_input()

    def get_input(self):
        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()
        self.root = self.widget_dict['root']['line_edit'].text()

    def on_line_edit_changed(self):
        self.get_input()
        info = {}
        if self.project_management == 'ftrack':
            info = {'api_server': self.api_server,
                    'api_key': self.api_key,
                    'api_user': self.api_user,
                    'company': self.company,
                    'api_script': self.api_script,
                    'project_management': 'ftrack',
                    'root': self.root
                    }
        if self.project_management == 'shotgun':
            info = {'api_server': self.api_server,
                    'api_key': self.api_key,
                    'api_user': self.api_user,
                    'api_script': self.api_script,
                    'company': self.company,
                    'project_management': 'shotgun',
                    'root': self.root
                    }
        elif self.project_management == 'lumbermill':
            info = {'api_server': self.api_server,
                    'api_key': self.api_key,
                    'api_user': self.api_user,
                    'api_script': self.api_script,
                    'company': self.company,
                    'project_management': 'lumbermill',
                    'root': self.root,
                    }
        if '' in info:
            self.ok_button.setEnabled(False)
        else:
            self.ok_button.setEnabled(True)
        self.contents = info

    def on_ok_clicked(self):
        self.accept()
        return self.contents

    def closeEvent(self, event):
        pass


class QuickSync(QtWidgets.QDialog):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        self.setWindowTitle('Lumbermill Quick Setup')
        self.default_globals = DEFAULT_GLOBALS
        self.default_user_globals = DEFAULT_USER_GLOBALS
        self.default_root = DEFAULT_ROOT
        self.default_code_root = DEFAULT_CODE_ROOT
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        size_policy.setVerticalStretch(1)
        layout = QtWidgets.QVBoxLayout(self)
        #layout.setSizePolicy(size_policy)
        grid_layout = QtWidgets.QGridLayout()
        button_layout = QtWidgets.QHBoxLayout()

        company_label = QtWidgets.QLabel('Company Name')
        root_label = QtWidgets.QLabel('CGL Root')
        code_root_label = QtWidgets.QLabel('Code Root')
        self.sync_options_label = QtWidgets.QLabel('<b>Sync Folders:</b>')
        self.sync_folder_label = QtWidgets.QLabel('Production Folder')
        self.sync_folder_message = QtWidgets.QLabel("<i>Don't worry you can edit this later</i>")
        self.sync_cgl_tools_label = QtWidgets.QLabel('CGL_TOOLS Folder')
        self.import_project_hint = QtWidgets.QLabel('<i>hint: Z:\COMPANIES\loneCoconut\source\CGL_TESTPROJECT - copies one project,'
                                                    '     Z:\COMPANIES\loneCoconut\source - copies all projects<\i>')
        self.import_project_hint.setSizePolicy(size_policy)
        self.import_project_hint.setWordWrap(True)

        self.company_line_edit = QtWidgets.QLineEdit()
        self.root_line_edit = QtWidgets.QLineEdit()
        self.code_root_line_edit = QtWidgets.QLineEdit()
        self.sync_folder_line_edit = QtWidgets.QLineEdit()
        self.sync_cgl_tools_line_edit = QtWidgets.QLineEdit()

        self.code_root_line_edit.setText(DEFAULT_CODE_ROOT)
        self.root_line_edit.setText(self.default_root)
        self.sync_cgl_tools_line_edit.setText(os.path.join(self.default_root, '_config', 'cgl_tools'))
        self.company_line_edit.setText('default')

        self.code_root_line_edit.setEnabled(False)
        # self.root_line_edit.setEnabled(False)
        self.sync_cgl_tools_line_edit.setEnabled(False)
        self.sync_folder_line_edit.setEnabled(False)

        self.aws_globals_label = QtWidgets.QLabel()
        # self.projects_checkbox = QtWidgets.QCheckBox('Import a Project')
        self.sync_thing_checkbox = QtWidgets.QCheckBox('Set up Remote Syncing')
        # self.import_label = QtWidgets.QLabel('Import Project From:')
        # self.import_line_edit = QtWidgets.QLineEdit()
        # self.import_button = QtWidgets.QToolButton()
        # self.import_button.setText('...')
        # self.sync_thing_checkbox.setChecked(True)
        self.sync_thing_checkbox.hide()
        # self.projects_checkbox.setChecked(True)

        self.company_name = 'Lone Coconut'
        self.company_name_s3 = 'lone-coconut'
        self.company_name_disk = 'loneCoconut'
        self.cgl_tools_path = os.path.join(DEFAULT_HOME, 'downloads', 'cgl_tools.zip')
        self.globals_path = os.path.join(DEFAULT_HOME, 'downloads', 'globals.json')
        self.aws_globals = r'https://%s.s3.amazonaws.com/globals.json' % self.company_name_s3
        self.check_for_globals_button = QtWidgets.QPushButton('Check for Globals')
        self.download_globals_button = QtWidgets.QPushButton('Set Up Lumbermill')

        button_layout.addStretch(1)
        button_layout.addWidget(self.download_globals_button)

        grid_layout.addWidget(root_label, 2, 0)
        grid_layout.addWidget(self.root_line_edit, 2, 1)
        grid_layout.addWidget(code_root_label, 3, 0)
        grid_layout.addWidget(self.code_root_line_edit, 3, 1)
        # grid_layout.addWidget(self.import_label, 4, 0)
        # grid_layout.addWidget(self.import_line_edit, 4, 1)
        # grid_layout.addWidget(self.import_button, 4, 2)
        # grid_layout.addWidget(self.import_project_hint, 5, 1)
        grid_layout.addWidget(self.sync_options_label, 6, 0)
        grid_layout.addWidget(self.sync_folder_label, 7, 0)
        grid_layout.addWidget(self.sync_folder_line_edit, 7, 1)
        grid_layout.addWidget(self.sync_folder_message, 8, 1)
        grid_layout.addWidget(self.sync_cgl_tools_label, 9, 0)
        grid_layout.addWidget(self.sync_cgl_tools_line_edit, 9, 1)

        layout.addWidget(company_label)
        layout.addWidget(self.company_line_edit)
        layout.addWidget(self.aws_globals_label)
        # layout.addWidget(self.projects_checkbox)
        layout.addWidget(self.sync_thing_checkbox)
        layout.addLayout(grid_layout)
        layout.addLayout(button_layout)
        layout.addStretch(1)
        self.aws_globals_label.hide()
        # self.on_projects_checkbox_clicked()
        self.on_sync_thing_checkbox_clicked()
        self.on_company_name_changed()

        self.company_line_edit.editingFinished.connect(self.on_company_name_changed)
        self.root_line_edit.textChanged.connect(self.on_root_changed)
        self.download_globals_button.clicked.connect(self.set_up_lumbermill)
        # self.projects_checkbox.clicked.connect(self.on_projects_checkbox_clicked)
        self.sync_thing_checkbox.clicked.connect(self.on_sync_thing_checkbox_clicked)
        # self.import_line_edit.editingFinished.connect(self.on_import_line_edit_changed)

    def on_root_changed(self):
        self.default_root = self.root_line_edit.text()
        self.sync_cgl_tools_line_edit.setText(os.path.join(self.default_root, '_config', 'cgl_tools'))
        self.default_globals = os.path.join(self.default_root, '_config', 'globals.json')

    def on_import_line_edit_changed(self):
        import re
        import_folder = self.import_line_edit.text()
        if 'source' in import_folder:
            context = 'source'
        elif 'render' in import_folder:
            context = 'render'
        else:
            print 'Not a valid folder to import'
            return
        first, second = import_folder.split(context)
        print first, second, 2
        company = os.path.split(os.path.dirname(first))[-1]
        if second:
            print 'second is', second
            splitty = os.path.split(second)
            print splitty, 0
            if re.search('\w', splitty[0]):
                project = splitty[0]
                print 'match'
            else:
                print 'no match'
                project = splitty[1]
            if not project:
                project = second.replace('\\', '').replace('/', '')
            project = project.replace('\\', '').replace('/', '')
            print project, 1
            sync_folder = os.path.join(self.default_root, company, 'source', project)
        else:
            sync_folder = os.path.join(self.default_root, company, 'source')
        self.sync_folder_line_edit.setText(sync_folder)

    def on_sync_thing_checkbox_clicked(self):
        if self.sync_thing_checkbox.checkState():
            self.sync_options_label.show()
            self.sync_folder_label.show()
            # self.sync_folder_message.show()
            self.sync_cgl_tools_label.show()
            self.sync_folder_line_edit.show()
            self.sync_cgl_tools_line_edit.show()
        else:
            self.sync_options_label.hide()
            self.sync_folder_label.hide()
            self.sync_folder_message.hide()
            self.sync_cgl_tools_label.hide()
            self.sync_folder_line_edit.hide()
            self.sync_cgl_tools_line_edit.hide()


    def on_company_name_changed(self):
        self.company_name = self.company_line_edit.text()
        if self.company_name:
            self.company_name_s3 = self.company_name.replace(' ', '-').replace('_', '-')
            self.company_name_disk = self.company_name_s3.replace('-', '_')
            self.aws_globals = r'https://%s.s3.amazonaws.com/globals.json' % self.company_name_s3
            if web.url_exists(self.aws_globals):
                self.aws_globals_label.setText('Found Shared Company Globals on Cloud')
                self.aws_globals_label.setStyleSheet("color: rgb(0, 255, 0);")
            else:
                self.aws_globals_label.setText('No Shared Globals Found - skipping')
                self.aws_globals_label.setStyleSheet("color: rgb(255, 0, 0);")
            self.aws_globals_label.show()

    def download_globals_from_cloud(self):

        if self.aws_globals_label.text() == 'Found Shared Company Globals on Cloud':
            globals_path = os.path.join(DEFAULT_HOME, 'downloads', 'globals.json')
            cgl_tools_path = os.path.join(DEFAULT_HOME, 'downloads', 'cgl_tools.zip')
            self.globals_path = globals_path
            self.cgl_tools_path = cgl_tools_path
            if not os.path.exists(os.path.dirname(globals_path)):
                os.makedirs(os.path.dirname(globals_path))
            if os.path.exists(globals_path):
                os.remove(globals_path)
            r = requests.get(self.aws_globals, allow_redirects=True)
            if '<Error>' in r.content:
                print('No File %s for company: %s' % (self.aws_globals, self.company_name))
            else:
                print('Saving Globals file to: %s' % globals_path)
                with open(globals_path, 'w+') as f:
                    f.write(r.content)
            self.accept()
            return True
        else:
            return False
            print('No Globals Found - Get your Studio to publish their globals, or Create new ones?')

    def edit_globals_paths(self):
        globals = read_write.load_json(self.globals_path)
        # change the stuff
        globals["paths"]["code_root"] = self.default_code_root
        globals["paths"]["root"] = self.default_root
        globals["paths"]["cgl_tools"] = os.path.join(self.default_root, '_config', 'cgl_tools')
        # TODO this shouldn't be used
        globals["paths"]["globals"] = os.path.join(self.default_root, '_config', 'globals.json')
        # TODO this should be a env_variable
        globals["paths"]["user_globals"] = self.default_user_globals
        globals["sync"]["syncthing"]["sheets_config_path"] = os.path.join(self.default_root, '_config', 'client.json')
        # TODO this should exist
        globals["account_info"]["globals_path"] = os.path.join(self.default_root, '_config', 'globals.json')
        # TODO - This shouldn't exist
        globals["cg_lumberjack_dir"] = os.path.join(self.default_root, '_config')
        # TODO - it'd be nice to double check all the sofwtare paths and see if there are newer versions on disk, this will help a ton.
        globals_dir = os.path.dirname(globals["paths"]["globals"])
        if not os.path.exists(globals_dir):
            os.makedirs(globals_dir)
        print 'Saving Globals To: %s' % globals["paths"]["globals"]
        read_write.save_json(globals["paths"]["globals"], globals)

    def setup_syncthing(self):
        """

        :return:
        """
        from cgl.ui.widgets.dialog import InputDialog

        cgl_tools_folder = os.path.join(self.default_root, '_config', 'cgl_tools')
        if not os.path.exists(cgl_tools_folder):
            os.makedirs(cgl_tools_folder)
        sync_folders = {r'[root]\_config\cgl_tools': os.path.join(cgl_tools_folder)}
        # TODO - need to set 2nd value here as a global in globals. sync_sheet: LONE_COCONUT_SYNC_THING
        # syncthing.setup_workstation()
        dialog = InputDialog(title='Sync Message', message='Your Machine has be submitted for approval for file sharing\n'
                                                           'After you have been added, click:\n'
                                                           ' Sync> Sync From Server\n'
                                                           'and you will start syncing folders')
        dialog.exec_()
        # syncthing.setup(self.company_name_s3, 'LONE_COCONUT_SYNC_THING', sync_folders)


    def set_up_lumbermill(self):
        """
        checks s3 for the existance of a globals file and pipeline_designer files.
        :return:
        """
        if self.download_globals_from_cloud():
            self.edit_globals_paths()
            create_user_globals(self.default_user_globals, self.default_globals)
        else:
            dialog = ConfigDialog(company=self.company_line_edit.text(), root=self.default_root)
            dialog.exec_()


def create_user_globals(user_globals, globals_path):
    if user_globals:
        if not os.path.exists(os.path.dirname(user_globals)):
            os.makedirs(os.path.dirname(user_globals))
        d = {
             "globals": globals_path,
             "previous_path": "",
             "previous_paths": {},
             "methodology": "local",
             "my_tasks": {}
             }
        print "saving user_globals to %s" % user_globals
        read_write.save_json(user_globals, d)
    else:
        print 'No Root Defined, cannot save user globals'


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    form = QuickSync()
    form.show()
    app.exec_()

