import os
import sys
import yaml
import json
import shutil


class InitializeConfig(object):
    """
    This creates globals for companies.
    """
    def __init__(self, default_company=None, default_pm='lumbermill', server_url=None, api_key=None, api_user=None,
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
        self.set_default_location()
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
        to_path = os.path.join(self.cgl_dir, 'global.yaml')
        if os.path.exists(self.cgl_dir):
            # make the "studio level" global.yaml
            if 'global.yaml' not in os.listdir(self.cgl_dir):
                shutil.copy2(base, to_path)
        else:
            os.makedirs(self.cgl_dir)
            shutil.copy2(base, to_path)

    def set_default_location(self):
        config = self._load_yaml(self.default_globals)
        config['account_info']['user_directory'] = self.cgl_dir
        self._write_yaml(self.default_globals, config)
        self._write_json(self.default_globals_json, config)

    def set_proj_management_details(self):
        if self.default_pm != 'lumbermill':
            config = self._load_yaml(self.default_globals)
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





