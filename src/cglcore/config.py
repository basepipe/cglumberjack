import os
import sys
import yaml
import json
import shutil
from Qt import QtWidgets, QtCore, QtGui


class InitializeConfig(object):
    """
    This creates globals for companies.
    """
    def __init__(self, default_company=None, default_pm='', server_url=None, api_key=None, api_user=None,
                 api_script=None):
        self.server_url = server_url
        self.api_key = api_key
        self.api_user = api_user
        self.api_script = api_script
        self.user_dir = os.path.expanduser("~")
        self.default_company = default_company
        self.default_pm = default_pm
        # first priority - figure out where the cgl_directory is going to be, or currently is.
        self.cgl_dir = self.get_default_cgl_dir()
        self.default_globals = os.path.join(self.cgl_dir, 'globals.yaml')
        self.default_globals_json = os.path.join(self.cgl_dir, 'globals.json')
        # Check for default globals, if they don't exist create them
        self.create_default_globals()
        # Set the default location in the globals
        #self.set_default_location()
        self.set_proj_management_details()

    def get_default_cgl_dir(self):
        if 'Documents' in self.user_dir:
            cg_lumberjack_dir = os.path.join(self.user_dir, 'cglumberjack')
        else:
            cg_lumberjack_dir = os.path.join(self.user_dir, 'Documents', 'cglumberjack')
        return cg_lumberjack_dir

    def create_default_globals(self):
        """
        Creates default globals in the correct direcgory if they don't exist - this will pull from the default CGL
        configuration.
        :return:
        """
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg", "global_template.yaml")
        to_path = os.path.join(self.cgl_dir, 'globals.yaml')
        if os.path.exists(self.cgl_dir):
            # make the "studio level" global.yaml
            if 'globals.yaml' not in os.listdir(self.cgl_dir):
                shutil.copy2(base, to_path)
        else:
            os.makedirs(self.cgl_dir)
            shutil.copy2(base, to_path)
        print 'Created Global: %s' % to_path

    def set_default_location(self):
        config = self._load_yaml(self.default_globals)
        config['account_info']['user_directory'] = self.cgl_dir
        self._write_yaml(self.default_globals, config)
        self._write_json(self.default_globals_json, config)

    def set_proj_management_details(self):
        if self.default_pm != 'lumbermill':
            from cglui.startup import do_gui_init

            print 1
            config = self._load_yaml(self.default_globals)
            app = do_gui_init()
            dialog = CheckGlobalsDialog(company=config['account_info']['company'],
                                        project_management=config['account_info']['project_management'],
                                        user_directory=config['account_info']['user_directory'])
            dialog.show()
            app.exec_()
            return
            if self.default_pm == 'ftrack':
                config['ftrack']['server_url'] = self.server_url
                config['ftrack']['api_key'] = self.api_key
                config['ftrack']['api_user'] = self.api_user
                self._write_yaml(self.default_globals, config)
                self._write_json(self.default_globals_json, config)
            elif self.default_pm == 'shotgun':
                config['shotgun']['url'] = self.server_url
                config['shotgun']['api_key'] = self.api_key
                config['shotgun']['api_script'] = self.api_script
                config['shotgun']['username'] = self.api_user
                self._write_yaml(self.default_globals, config)
                self._write_json(self.default_globals_json, config)

    @staticmethod
    def _load_yaml(path):
        with open(path, 'r') as stream:
            try:
                result = yaml.load(stream)
                if result:
                    return result
                else:
                    return {}
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit(99)

    @staticmethod
    def _write_yaml(filepath, data):
        with open(filepath, 'w') as yaml_file:
            yaml.dump(data, yaml_file)

    @staticmethod
    def _write_json(filepath, data):
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data


class Configuration(object):
    """

    This asssumes that proper config files are in place - at minimum a default globals script to read from.

    """
    LOADED_CONFIG = {}
    user_dir = os.path.expanduser("~")
    if 'Documents' in user_dir:
        cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack')
    else:
        cg_lumberjack_dir = os.path.join(user_dir, 'Documents', 'cglumberjack')
    user_config = os.path.join(cg_lumberjack_dir, 'user_config.yaml')

    def __init__(self, company=None, proj_management=None):
        self.proj_management = None
        if proj_management:
            self.proj_management = proj_management
        if company:
            Configuration.LOADED_CONFIG = {}
        if not Configuration.LOADED_CONFIG:
            self.make_cglumberjack_dir()
            if company:
                self.company_global_dir = os.path.join(self.cg_lumberjack_dir, 'companies', company)
            else:
                self.company_global_dir = None
            global_cfg, app_cfg = self._find_config_file()
            print 'Global Config:', global_cfg
            cfg = {}
            cfg['cg_lumberjack_dir'] = self.cg_lumberjack_dir
            if os.path.isfile(global_cfg):
                cfg.update(self._load_yaml(global_cfg))
            if os.path.isfile(app_cfg):
                cfg.update(self._load_yaml(app_cfg))
            Configuration.LOADED_CONFIG['app'] = cfg

    def make_cglumberjack_dir(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg", "global_template.yaml")
        to_path = os.path.join(self.cg_lumberjack_dir, 'global.yaml')
        if os.path.exists(self.cg_lumberjack_dir):
            # make the "studio level" global.yaml
            if 'global.yaml' not in os.listdir(self.cg_lumberjack_dir):
                shutil.copy2(base, to_path)
        else:
            os.makedirs(self.cg_lumberjack_dir)
            shutil.copy2(base, to_path)

    def make_company_global_dir(self):
        default_global = os.path.join(self.cg_lumberjack_dir, 'global.yaml')
        to_path = os.path.join(self.company_global_dir, 'global.yaml')
        if os.path.exists(self.company_global_dir):
            print 'Copying from %s to %s' % (default_global, to_path)
            if 'global.yaml' not in os.listdir(self.company_global_dir):
                shutil.copy2(default_global, to_path)
                if self.proj_management:
                    self.update_proj_management()
        else:
            print '%s does not exist' % self.company_global_dir
            os.makedirs(self.company_global_dir)
            shutil.copy2(default_global, to_path)
            if self.proj_management:
                self.update_proj_management()

    def update_proj_management(self):
        yaml_file = os.path.join(self.company_global_dir, 'global.yaml')
        config_dict = self._load_yaml(yaml_file)
        config_dict['account_info']['project_management'] = self.proj_management
        self._write_yaml(yaml_file, config_dict)

    def _find_config_file(self):
        template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg")
        app_name = os.path.basename(sys.argv[0])
        # this doesn't seem to be used but it's a great idea
        app_cfg = os.path.join(template_folder, os.path.splitext(app_name)[0] + ".yaml")
        if self.company_global_dir:
            if os.path.exists(self.company_global_dir):
                global_cfg = os.path.join(self.company_global_dir, 'global.yaml')
                if not os.path.exists(global_cfg):
                    self.make_company_global_dir()
            else:
                self.make_company_global_dir()
                global_cfg = os.path.join(self.company_global_dir, 'global.yaml')
        else:
            if os.path.exists(self.cg_lumberjack_dir):
                global_cfg = os.path.join(self.cg_lumberjack_dir, 'global.yaml')
            else:
                self.make_cglumberjack_dir()
                global_cfg = os.path.join(self.cg_lumberjack_dir, 'global.yaml')

        print 'Global Config Location: ', global_cfg
        return global_cfg, app_cfg

    @staticmethod
    def _load_yaml(path):
        with open(path, 'r') as stream:
            try:
                result = yaml.load(stream)
                if result:
                    return result
                else:
                    return {}
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit(99)

    @staticmethod
    def _write_yaml(filepath, config_dict=None):
        with open(filepath, 'w') as yaml_file:
            yaml.dump(config_dict, yaml_file)


class UserConfig(object):
    user_config_path = Configuration().user_config

    def __init__(self, company=None, user_email=None, user_name=None, current_path=None):
        if os.path.exists(self.user_config_path):
            self.d = self._load_yaml(self.user_config_path)
        else:
            return None
        self.current_path = current_path
        if company:
            self.company = company
        else:
            self.company = self.d['company']
        if user_email:
            self.user_email = user_email
        else:
            self.user_email = self.d['user_email']
        if user_name:
            self.user_name = user_name
        else:
            self.user_name = self.d['user_name']

    def update_all(self):
        self.update_path()
        self.update_user_email()
        self.update_user_name()
        self.update_company()
        self._write_yaml()

    def update_path(self):
        if self.current_path:
            self.d['previous_path'] = self.current_path
            number = 1
            try:
                if self.current_path in self.d['previous_paths']:
                    number = self.d['previous_paths'][self.current_path]
                    number += 1
                self.d['previous_paths'][self.current_path] = number
            except KeyError:
                self.d['previous_paths'] = {self.current_path: number}

    def update_user_email(self):
        if self.user_email:
            self.d['user_email'] = self.user_email

    def update_user_name(self):
        if self.user_name:
            self.d['user_name'] = self.user_name

    def update_company(self):
        if self.company:
            self.d['company'] = self.company

    def _write_yaml(self):
        with open(self.user_config_path, 'w') as f:
            yaml.dump(self.d, f, default_flow_style=False)

    @staticmethod
    def _load_yaml(path):
        with open(path, 'r') as stream:
            try:
                result = yaml.load(stream)
                if result:
                    return result
                else:
                    return {}
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit(99)


class CheckGlobalsDialog(QtWidgets.QDialog):

    def __init__(self, company, project_management, user_directory):
        QtWidgets.QDialog.__init__(self)
        self.proj_management_label = QtWidgets.QLabel('Project Management')
        self.contents = {}
        self.company = company
        layout = QtWidgets.QVBoxLayout(self)
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['', 'lumbermill', 'ftrack', 'shotgun', 'google_docs'])
        self.red_palette = QtGui.QPalette()
        self.red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.green_palette = QtGui.QPalette()
        self.green_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 255, 0))
        self.black_palette = QtGui.QPalette()
        self.black_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 0, 0))

        self.server_label = QtWidgets.QLabel('server url:')
        self.api_key_label = QtWidgets.QLabel('api key:')
        self.api_user_label = QtWidgets.QLabel('api user:')
        self.api_script_label = QtWidgets.QLabel('api script:')
        self.server_line_edit = QtWidgets.QLineEdit()
        self.api_key_line_edit = QtWidgets.QLineEdit()
        self.api_user_line_edit = QtWidgets.QLineEdit()
        self.api_script_line_edit = QtWidgets.QLineEdit()

        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.button = ''
        self.ok_button.setEnabled(False)


        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        proj_label = QtWidgets.QLabel('Your Company')
        self.proj_line_edit = QtWidgets.QLineEdit()
        self.message = QtWidgets.QLabel()

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.addWidget(proj_label, 0, 0)
        self.grid_layout.addWidget(self.proj_line_edit, 0, 1)
        self.grid_layout.addWidget(self.proj_management_label, 2, 0)
        self.grid_layout.addWidget(self.proj_management_combo, 2, 1)
        self.grid_layout.addWidget(self.server_label, 3, 0)
        self.grid_layout.addWidget(self.server_line_edit, 3, 1)
        self.grid_layout.addWidget(self.api_key_label, 4, 0)
        self.grid_layout.addWidget(self.api_key_line_edit, 4, 1)
        self.grid_layout.addWidget(self.api_user_label, 5, 0)
        self.grid_layout.addWidget(self.api_user_line_edit, 5, 1)
        self.grid_layout.addWidget(self.api_script_label, 6, 0)
        self.grid_layout.addWidget(self.api_script_line_edit, 6, 1)

        layout.addLayout(self.grid_layout)
        layout.addWidget(self.message)
        layout.addLayout(button_layout)

        self.proj_management_combo.currentIndexChanged.connect(self.on_pm_changed)
        self.server_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_user_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_script_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_key_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.get_input()
        self.hide_api_info()

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
        if self.proj_management_combo.currentText() == 'lumbermill':
            self.hide_api_info()
        elif self.proj_management_combo.currentText() == 'ftrack':
            self.show_api_info()
        elif self.proj_management_combo.currentText() == 'shotgun':
            self.show_api_info()
            self.api_script.show()
            self.api_script_line_edit.show()
        self.get_input()
            
    def get_input(self):
        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()
        self.company = self.proj_line_edit.text()

    def on_line_edit_changed(self):
        # TODO make these dictionairies
        self.get_input()
        if self.project_management == 'ftrack':
            info = [self.api_server, self.api_key, self.api_user, self.company]
        if self.project_management == 'shotgun':
            info = [self.api_server, self.api_key, self.api_user, self.api_script, self.company]
        elif self.project_management == 'lumbermill':
            info = [self.company]
        if '' in info:
            self.ok_button.setEnabled(False)
        else:
            self.ok_button.setEnabled(True)
        self.contents = {self.project_management: info}

    def on_ok_clicked(self):
        print self.contents
        return self.contents
        


def config():
    """
    get the whole configuration

    Returns: dict


    """
    return Configuration().LOADED_CONFIG


def app_config(company=None, proj_management=None):
    """
    get the app configuration

    Returns: dict

    """
    return Configuration(company=company, proj_management=proj_management).LOADED_CONFIG['app']


def user_config():
    """
    get the location of the user_config()
    :return: string of path
    """
    return Configuration().user_config





