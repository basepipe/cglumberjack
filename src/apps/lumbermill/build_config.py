from Qt import QtCore, QtWidgets, QtGui
from cglui.widgets.containers.dict_tree import DictionaryTreeWidget
import getpass
import os
import json
import shutil


class PathItemWidget(QtWidgets.QWidget):
    line_edit_changed = QtCore.Signal(object)

    def __init__(self, parent=None, paths_dict={}, hide_on_find=True):
        QtWidgets.QWidget.__init__(self, parent)
        self.layout = QtWidgets.QGridLayout(self)
        self.user_dir = os.path.expanduser("~")
        self.user_name = self.get_user_name()
        self.cgl_dir = self.get_default_cgl_dir()
        self.user_globals_path = self.get_user_config(self.cgl_dir)
        i = -1
        self.red_palette = QtGui.QPalette()
        self.red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.green_palette = QtGui.QPalette()
        self.green_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 255, 0))
        self.black_palette = QtGui.QPalette()
        self.black_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 0, 0))
        self.cgl_tools_folder = None
        self.widget_dict = {}

        for key in paths_dict:
            i += 1
            label = QtWidgets.QLabel(key)
            line_edit = QtWidgets.QLineEdit()

            line_edit.setText(paths_dict[key])
            folder_button = QtWidgets.QToolButton()
            if key == 'cgl_tools':
                self.cgl_tools_folder = folder_button
            folder_button.setIcon(QtGui.QIcon(self.icon_path('folder24px.png')))
            folder_button.line_edit = line_edit
            folder_button.label = label
            message = QtWidgets.QLabel('Path Not Found, Please Specify %s' % key)
            message.setPalette(self.red_palette)
            folder_button.message = message
            self.widget_dict[key] = {'label': label,
                                     'line_edit': line_edit,
                                     'message': message}
            self.layout.addWidget(label, i, 0)
            self.layout.addWidget(line_edit, i, 1)
            self.layout.addWidget(folder_button, i, 2)
            i += 1
            self.layout.addWidget(message, i, 1)
            folder_button.clicked.connect(self.on_path_chosen)
            self.check_path(key, label, line_edit, message, folder_button, hide_on_find=hide_on_find)
            line_edit.textChanged.connect(lambda: self.on_line_edit_changed(key))

    @staticmethod
    def icon_path(filename):
        this = __file__.split('src')[0]
        return os.path.join(this, 'resources', 'icons', filename)

    def on_line_edit_changed(self, key):
        self.line_edit_changed.emit({key: self.sender()})

    def check_path(self, path_name, label, line_edit, message, folder_button, hide_on_find):
        path_ = line_edit.text()
        if os.path.exists(path_):
            line_edit.setEnabled(False)
            message.setText('%s Found Path, Ready for Ass Kicking!' % path_name)
            message.setPalette(self.black_palette)
            if hide_on_find:
                label.hide()
                line_edit.hide()
                message.hide()
                folder_button.hide()
        else:
            if path_name == 'cgl_tools':
                line_edit.setEnabled(False)
                message.setText('%s Path Not Found, set "root"!' % path_name)
                if hide_on_find:
                    label.hide()
                    line_edit.hide()
                    message.hide()
                    folder_button.hide()
            elif path_name == 'code_root':
                code_root = __file__.split('src')[0]
                line_edit.setEnabled(False)
                line_edit.setText(code_root)
                message.setText('%s Path Found, Ready for Ass Kicking!' % path_name)
                message.setPalette(self.black_palette)
                if hide_on_find:
                    label.hide()
                    line_edit.hide()
                    message.hide()
                    folder_button.hide()
            elif path_name == 'user_globals':
                line_edit.setText(self.user_globals_path)
                line_edit.setEnabled(False)
                message.setText('Setting As Default Location, Click Folder Button to Change')
                message.setPalette(self.black_palette)
            elif path_name == 'globals':
                line_edit.setEnabled(False)
                message.setText('%s Path Not Found, set "root"!' % path_name)

    def on_path_chosen(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory()
        self.sender().line_edit.setText(folder)
        self.check_path(folder, self.sender().label, self.sender().line_edit, self.sender().message, self.sender(),
                        hide_on_find=False)
        if self.sender().label.text() == 'root':
            self.cgl_tools_folder.line_edit.setText(os.path.join(folder, '_config', 'cgl_tools'))
            self.cgl_tools_folder.message.setText('%s Path Found, Ready for Ass Kicking!' % 'cgl_tools')
            self.cgl_tools_folder.message.setPalette(self.black_palette)

            self.widget_dict['globals']['line_edit'].setText(os.path.join(folder, '_config', 'globals.json'))
            self.widget_dict['globals']['message'].setText('%s Path Found, Ready for Ass Kicking!' % 'globals')
            self.widget_dict['globals']['message'].setPalette(self.black_palette)


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

    def __init__(self, parent=None, company='', project_management='lumbermill', user_directory='', config_dict={}):
        QtWidgets.QDialog.__init__(self, parent)
        self.app_config = config_dict
        self.proj_management_label = QtWidgets.QLabel('Project Management')
        self.contents = {}
        self.company = company
        self.global_config = {}
        self.root = ''
        self.user_name = self.get_user_name()

        layout = QtWidgets.QVBoxLayout(self)
        self.poject_management_label = QtWidgets.QLabel('Project Management:')
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['', 'lumbermill', 'ftrack', 'shotgun'])
        self.red_palette = QtGui.QPalette()
        self.red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.green_palette = QtGui.QPalette()
        self.green_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 255, 0))
        self.black_palette = QtGui.QPalette()
        self.black_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 0, 0))

        self.user_email_label = QtWidgets.QLabel('User Email:')
        self.user_email_line_edit = QtWidgets.QLineEdit()
        self.user_name_label = QtWidgets.QLabel('User Name:')
        self.user_name_line_edit = QtWidgets.QLineEdit()
        self.user_name_line_edit.setText(self.user_name)

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

        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()

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

        # self.project_management = self.app_config['account_info']['project_management']

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.create_globals_button)
        button_layout.addWidget(self.ok_button)

        self.globals_tree_widget = DictionaryTreeWidget({})
        this = __file__.split('src')[0]
        dict_ = self._load_json(os.path.join(this, 'src', 'cfg', 'global_template.json'))
        self.path_item_widget = PathItemWidget(paths_dict=dict_['paths'], hide_on_find=True)
        self.widget_dict = self.path_item_widget.widget_dict
        layout.addWidget(self.path_item_widget)
        # layout.addWidget(QHLine())
        layout.addLayout(self.proj_man_grid)
        layout.addWidget(self.globals_tree_widget)
        # layout.addWidget(QHLine())
        layout.addLayout(button_layout)

        # self.user_globals_line_edit.setEnabled(False)
        self.proj_management_combo.currentIndexChanged.connect(self.on_pm_changed)
        self.path_item_widget.line_edit_changed.connect(self.on_line_edits_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.create_globals_button.clicked.connect(self.on_create_globals_clicked)
        self.get_input()
        self.hide_api_info()
        self.on_pm_changed()
        self.check_user_config()
        self.globals_tree_widget.hide()
        self.on_globals_changed()

    @staticmethod
    def get_user_name():
        """
            find the currently logged in user
            Returns:
                str: username

        """
        return getpass.getuser()

    def on_line_edits_changed(self, data):
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
        src = os.path.join(self.widget_dict['code_root']['line_edit'].text(), 'src', 'cfg', 'cgl_tools')
        dst = os.path.join(self.widget_dict['cgl_tools']['line_edit'].text())
        shutil.copytree(src, dst)

    def create_global_config(self):
        if self.global_config:
            self.global_config['paths']['root'] = self.widget_dict['root']['line_edit'].text()
            self.global_config['paths']['cgl_tools'] = self.widget_dict['cgl_tools']['line_edit'].text()
            self.global_config['paths']['code_root'] = self.widget_dict['code_root']['line_edit'].text()
            self.global_config['account_info']['project_management'] = self.project_management
            self.global_config['account_info']['globals_path'] = self.widget_dict['globals']['line_edit'].text()
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
            if not os.path.exists(os.path.dirname(self.widget_dict['root']['line_edit'].text())):
                os.makedirs(os.path.dirname(self.widget_dict['root']['line_edit'].text()))
            self._write_json(self.widget_dict['globals']['line_edit'].text(), self.global_config)
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
                 "proj_man_user_name": ""
                 }
            self._write_json(user_globals, d)
        else:
            print 'No Root Defined, cannot save user globals'

    def load_user_config(self):
        pass

    def load_globals(self):
        globals_line_edit = self.widget_dict['globals']['line_edit']
        if globals_line_edit.text():
            globals_ = globals_line_edit.text()
            self.global_config = self._load_json(globals_)
            self.globals_tree_widget.load_dictionary(self.global_config)
            self.globals_tree_widget.show()
        return self.global_config

    def load_globals_template(self):
        code_root_line_edit = self.widget_dict['code_root']['line_edit']
        if code_root_line_edit.text():
            globals_ = os.path.join(code_root_line_edit.text(), 'src', 'cfg', 'global_template.json')
            self.global_config = self._load_json(globals_)
            self.globals_tree_widget.load_dictionary(self.global_config)
            self.globals_tree_widget.show()
            return self.global_config
        else:
            print 'Code Root Not Defined'
            return None

    def check_user_config(self):
        pass

    def cancel_clicked(self):
        self.accept()

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