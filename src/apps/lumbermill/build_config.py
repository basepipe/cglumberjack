from Qt import QtCore, QtWidgets, QtGui
from cglui.widgets.containers.dict_tree import DictionaryTreeWidget
import getpass
import os
import json
import shutil


class ConfigDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, company='', project_management='lumbermill', user_directory='', config_dict={}):
        QtWidgets.QDialog.__init__(self, parent)
        self.app_config = config_dict
        self.proj_management_label = QtWidgets.QLabel('Project Management')
        self.contents = {}
        self.company = company
        self.global_config = {}
        self.root = ''
        self.user_dir = os.path.expanduser("~")
        self.user_name = self.get_user_name()
        self.cgl_dir = self.get_default_cgl_dir()
        self.user_globals_path = self.get_user_config(self.cgl_dir)
        layout = QtWidgets.QVBoxLayout(self)
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['', 'lumbermill', 'ftrack', 'shotgun'])
        self.red_palette = QtGui.QPalette()
        self.red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.green_palette = QtGui.QPalette()
        self.green_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 255, 0))
        self.black_palette = QtGui.QPalette()
        self.black_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 0, 0))

        user_config = QtWidgets.QLabel('<b>User Settings:</b>')
        global_config_label = QtWidgets.QLabel('<b>Global Config:</b>')
        company_label = QtWidgets.QLabel('Company:')
        self.user_globals_label = QtWidgets.QLabel('User Config Location:')
        self.user_globals_line_edit = QtWidgets.QLineEdit()
        self.user_globals_line_edit.setText(self.user_globals_path)
        self.user_email_label = QtWidgets.QLabel('User Email:')
        self.user_email_line_edit = QtWidgets.QLineEdit()
        self.user_name_label = QtWidgets.QLabel('User Name:')
        self.user_name_line_edit = QtWidgets.QLineEdit()
        self.user_name_line_edit.setText(self.user_name)
        self.globals_label = QtWidgets.QLabel('Global Config Location:')
        self.globals_line_edit = QtWidgets.QLineEdit()
        self.company_line_edit = QtWidgets.QLineEdit()
        self.server_label = QtWidgets.QLabel('server url:')
        self.api_key_label = QtWidgets.QLabel('api key:')
        self.api_user_label = QtWidgets.QLabel('api user:')
        self.api_script_label = QtWidgets.QLabel('api script:')
        self.root_label = QtWidgets.QLabel('Production Root:')
        self.server_line_edit = QtWidgets.QLineEdit()
        self.api_key_line_edit = QtWidgets.QLineEdit()
        self.api_user_line_edit = QtWidgets.QLineEdit()
        self.api_script_line_edit = QtWidgets.QLineEdit()
        self.root_line_edit = QtWidgets.QLineEdit()

        self.code_root_label = QtWidgets.QLabel('Code Root:')
        self.code_root_line_edit = QtWidgets.QLineEdit()
        self.cgl_tools_label = QtWidgets.QLabel('cgl_tools location:')
        self.cgl_tools_line_edit = QtWidgets.QLineEdit()

        self.choose_folder_button = QtWidgets.QToolButton()
        self.choose_folder_button.setText('...')
        self.choose_root = QtWidgets.QToolButton()
        self.choose_root.setText('...')
        self.choose_code_root_button = QtWidgets.QToolButton()
        self.choose_code_root_button.setText('...')

        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.button = ''
        self.ok_button.setEnabled(False)
        self.create_globals_button = QtWidgets.QPushButton('Create Globals')

        self.root_message = QtWidgets.QLabel('Choose Root Folder')
        self.root_message.setPalette(self.red_palette)
        self.user_config_message = QtWidgets.QLabel('User Globals will be created')
        self.user_config_message.setPalette(self.red_palette)
        self.globals_message = QtWidgets.QLabel('Company globals will be created')
        self.globals_message.setPalette(self.red_palette)
        self.create_user_config_button = QtWidgets.QPushButton('Create User Globals')
        self.company_name_message = QtWidgets.QLabel('Enter Company Name to Continue')
        self.user_name_message = QtWidgets.QLabel('Username Does not match system user name')
        self.email_message = QtWidgets.QLabel('Enter Email to Continue')
        self.code_root_message = QtWidgets.QLabel('Choose Code Root Folder')
        self.code_root_message.setPalette(self.red_palette)
        self.proj_management_message = QtWidgets.QLabel('Choose Project Management')
        self.proj_management_message.setPalette(self.red_palette)
        # self.root_line_edit.setText(self.app_config['paths']['root'])
        # self.company_line_edit.setText(self.app_config['account_info']['default_company'])
        # self.project_management = self.app_config['account_info']['project_management']


        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.create_globals_button)
        button_layout.addWidget(self.ok_button)

        self.message = QtWidgets.QLabel()
        self.user_grid_layout = QtWidgets.QGridLayout()
        self.user_grid_layout.addWidget(user_config, 0, 0)
        self.user_grid_layout.addWidget(self.root_label, 1, 0)
        self.user_grid_layout.addWidget(self.root_line_edit, 1, 1)
        self.user_grid_layout.addWidget(self.choose_root, 1, 2)
        self.user_grid_layout.addWidget(self.root_message, 2, 1)
        self.user_grid_layout.addWidget(self.user_globals_label, 3, 0)
        self.user_grid_layout.addWidget(self.user_globals_line_edit, 3, 1)
        self.user_grid_layout.addWidget(self.user_config_message, 4, 1)
        self.user_grid_layout.addWidget(self.globals_label, 5, 0)
        self.user_grid_layout.addWidget(self.globals_line_edit, 5, 1)
        self.user_grid_layout.addWidget(self.globals_message, 6, 1)
        self.user_grid_layout.addWidget(self.cgl_tools_label, 7, 0)
        self.user_grid_layout.addWidget(self.cgl_tools_line_edit, 7, 1)
        self.user_grid_layout.addWidget(self.code_root_label, 8, 0)
        self.user_grid_layout.addWidget(self.code_root_line_edit, 8, 1)
        self.user_grid_layout.addWidget(self.choose_code_root_button, 8, 2)
        self.user_grid_layout.addWidget(self.code_root_message, 9, 1)

        self.user_grid_layout.addWidget(self.user_name_label, 10, 0)
        self.user_grid_layout.addWidget(self.user_name_line_edit, 10, 1)
        self.user_grid_layout.addWidget(self.user_email_label, 11, 0)
        self.user_grid_layout.addWidget(self.user_email_line_edit, 11, 1)

        self.user_grid_layout.addWidget(self.proj_management_label, 12, 0)
        self.user_grid_layout.addWidget(self.proj_management_combo, 12, 1)
        self.user_grid_layout.addWidget(self.proj_management_message, 13, 1)
        self.user_grid_layout.addWidget(self.api_key_line_edit, 14, 1)
        self.user_grid_layout.addWidget(self.api_key_label, 14, 0)
        self.user_grid_layout.addWidget(self.api_user_label, 15, 0)
        self.user_grid_layout.addWidget(self.api_user_line_edit, 15, 1)
        self.user_grid_layout.addWidget(self.server_label, 16, 0)
        self.user_grid_layout.addWidget(self.server_line_edit, 16, 1)




        self.globals_tree_widget = DictionaryTreeWidget({})
        layout.addLayout(self.user_grid_layout)
        layout.addWidget(self.message)
        layout.addWidget(self.globals_tree_widget)
        layout.addLayout(button_layout)
        self.hide_all()

        self.user_globals_line_edit.setEnabled(False)
        self.globals_line_edit.setEnabled(False)
        self.proj_management_combo.currentIndexChanged.connect(self.on_pm_changed)
        self.server_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_user_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_script_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_key_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.choose_root.clicked.connect(self.on_get_folder_clicked)
        self.choose_code_root_button.clicked.connect(self.on_choose_code_root_clicked)
        self.root_line_edit.textChanged.connect(self.on_root_changed)
        self.user_globals_line_edit.textChanged.connect(self.on_user_config_changed)
        self.globals_line_edit.textChanged.connect(self.on_globals_changed)
        self.create_globals_button.clicked.connect(self.on_create_globals_clicked)
        self.code_root_line_edit.textChanged.connect(self.on_code_root_changed)
        self.get_input()
        self.hide_api_info()
        self.on_pm_changed()
        self.check_user_config()

    def on_code_root_changed(self):
        code_root = self.code_root_line_edit.text()
        if os.path.exists(code_root):
            self.code_root_message.hide()
            self.load_globals_template()

    def on_globals_changed(self):
        config = self.globals_line_edit.text()
        if os.path.exists(config):
            self.globals_message.hide()
            self.global_config = self.load_globals()
        else:
            self.global_config = self.load_globals_template()

    def on_user_config_changed(self):
        config = self.user_globals_line_edit.text()
        if os.path.exists(config):
            self.user_config_message.hide()

    def on_root_changed(self):
        root = self.root_line_edit.text()
        if root:
            global_config_dir = os.path.join(root, '_config', 'globals.json')
            cgl_tools_dir = os.path.join(root, '_config', 'cgl_tools')
            self.cgl_tools_line_edit.setText(cgl_tools_dir)
            self.globals_line_edit.setText(global_config_dir)
            if os.path.exists(root):
                self.root_message.hide()
                self.globals_line_edit.show()
                #self.globals_message.show()
                self.globals_label.show()
                #self.user_config_message.show()
                self.proj_management_message.show()
                self.user_globals_label.show()
                self.user_globals_line_edit.show()
                self.create_globals_button.show()
                self.code_root_label.show()
                self.code_root_line_edit.show()
                self.cgl_tools_label.show()
                self.cgl_tools_line_edit.show()
                self.choose_code_root_button.show()
                self.proj_management_combo.show()
                self.proj_management_label.show()
            else:
                self.root_message.show()
                self.root_message.setText('root: %s will be created' % root)

    def on_create_globals_clicked(self):
        self.copy_cgl_tools()
        self.create_global_config()
        self.create_user_globals()
        if self.project_management == 'ftrack':
            # eed a wayto inherit thte task di
            import plugins.project_management.ftrack.setup_tasks as setup_tasks
            form = setup_tasks.TaskSetupGUI()
            form.exec_()
        self.accept()

    def copy_cgl_tools(self):
        src = os.path.join(self.code_root_line_edit.text(), 'src', 'cfg', 'cgl_tools')
        dst = os.path.join(self.cgl_tools_line_edit.text())
        shutil.copytree(src, dst)

    def create_global_config(self):
        if self.global_config:
            self.global_config['paths']['root'] = self.root_line_edit.text()
            self.global_config['paths']['cgl_tools'] = self.cgl_tools_line_edit.text()
            self.global_config['paths']['code_root'] = self.code_root_line_edit.text()
            self.global_config['account_info']['project_management'] = self.project_management
            self.global_config['account_info']['globals_path'] = self.globals_line_edit.text()
            if self.project_management == 'ftrack':
                self.global_config['project_management'][self.project_management]['api']['api_key'] = self.api_key_line_edit.text()
                self.global_config['project_management'][self.project_management]['api']['server_url'] = self.server_line_edit.text()
                self.global_config['project_management'][self.project_management]['api']['api_user'] = self.api_user_line_edit.text()
                self.global_config['project_management'][self.project_management]['api']['default_schema'] = 'VFX'
            elif self.project_management == 'shotgun':
                self.global_config['project_management'][self.project_management]['api']['api_key'] = self.api_key_line_edit.text()
                self.global_config['project_management'][self.project_management]['api']['server_url'] = self.server_line_edit.text()
                self.global_config['project_management'][self.project_management]['api']['api_user'] = self.api_user_line_edit.text()
                self.global_config['project_management'][self.project_management]['api']['api_script'] = self.api_script_line_edit.text()
            if not os.path.exists(os.path.dirname(self.globals_line_edit.text())):
                os.makedirs(os.path.dirname(self.globals_line_edit.text()))
            self._write_json(self.globals_line_edit.text(), self.global_config)
        else:
            print 'No Dictionary Loaded for Global Config'


    def check_user_config_exists(self):
        config = self.user_globals_line_edit.text()
        if os.path.exists(config):
            self.user_config_message.hide()
            self.create_user_config_button.hide()

    def create_user_globals(self):
        if self.user_globals_line_edit.text():
            if not os.path.exists(os.path.dirname(self.user_globals_line_edit.text())):
                os.makedirs(os.path.dirname(self.user_globals_line_edit.text()))
            d = {
                 "globals": self.globals_line_edit.text(),
                 "previous_path": "",
                 "previous_paths": {},
                 "user_email": self.user_email_line_edit.text(),
                 "user_name": self.user_name_line_edit.text(),
                 "proj_man_user_email": self.api_user_line_edit.text(),
                 "proj_man_user_name": ""
                 }
            self._write_json(self.user_globals_line_edit.text(), d)
        else:
            print 'No Root Defined, cannot save user globals'

    def load_user_config(self):
        pass

    def load_globals(self):
        if self.globals_line_edit.text():
            globals_ = self.globals_line_edit.text()
            self.global_config = self._load_json(globals_)
            self.globals_tree_widget.load_dictionary(self.global_config)
            self.globals_tree_widget.show()
        return self.global_config

    def load_globals_template(self):
        if self.code_root_line_edit.text():
            globals_ = os.path.join(self.code_root_line_edit.text(), 'src', 'cfg', 'global_template.json')
            self.global_config = self._load_json(globals_)
            self.global_config
            self.globals_tree_widget.load_dictionary(self.global_config)
            self.globals_tree_widget.show()
            return self.global_config
        else:
            print 'Code Root Not Defined'
            return None

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

    def check_user_config(self):
        pass

    def on_choose_code_root_clicked(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory()
        self.code_root_line_edit.setText(folder)

    def on_get_folder_clicked(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory()
        self.root_line_edit.setText(folder)

    def cancel_clicked(self):
        self.accept()

    def hide_all(self):
        self.root_message.hide()
        self.user_globals_label.hide()
        self.user_globals_line_edit.hide()
        self.user_config_message.hide()
        self.globals_message.hide()
        self.user_name_label.hide()
        self.user_name_line_edit.hide()
        self.user_email_label.hide()
        self.user_email_line_edit.hide()
        self.code_root_label.hide()
        self.code_root_line_edit.hide()
        self.choose_code_root_button.hide()
        self.cgl_tools_label.hide()
        self.cgl_tools_line_edit.hide()
        self.proj_management_message.hide()

        self.proj_management_label.hide()
        self.proj_management_combo.hide()
        self.api_key_line_edit.hide()
        self.api_key_label.hide()
        self.api_user_label.hide()
        self.api_user_line_edit.hide()
        self.server_label.hide()
        self.server_line_edit.hide()
        self.globals_label.hide()
        self.globals_line_edit.hide()
        self.globals_tree_widget.hide()
        self.ok_button.hide()
        self.cancel_button.hide()
        self.create_globals_button.hide()

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

    def on_pm_changed(self):
        self.api_key_line_edit.setText('')
        self.api_script_line_edit.setText('')
        self.api_user_line_edit.setText('')
        self.server_line_edit.setText('')
        self.project_management = self.proj_management_combo.currentText()
        if self.project_management == 'lumbermill':
            self.hide_api_info()
            self.proj_management_message.hide()
        elif self.project_management == 'ftrack':
            self.show_api_info()
            self.proj_management_message.hide()
        elif self.project_management == 'shotgun':
            self.show_api_info()
            self.api_script_label.show()
            self.api_script_line_edit.show()
            self.proj_management_message.hide()
        elif self.project_management == '':
            self.hide_api_info()
        self.get_input()

    def get_input(self):
        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()
        self.company = self.company_line_edit.text()
        self.root = self.root_line_edit.text()

    def on_line_edit_changed(self):
        # TODO make these dictionairies
        self.get_input()

        print self.project_management

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

    @staticmethod
    def _write_json(filepath, data):
        print 'writing json to %s' % filepath
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data

    def closeEvent(self, event):
        pass


if __name__ == "__main__":
    app = QtGui.QApplication([])
    form = ConfigDialog()
    form.show()
    app.exec_()
