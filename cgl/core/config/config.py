import os
import re
import glob
from cgl.core.utils.read_write import load_json, save_json


def get_user_config_file():
    """
    returns the location of the user config file.
    :return:
    """
    return os.getenv('cgl_user_globals')


def user_config():
    """
    returns dictionary representing user config.
    :return:
    """
    if os.path.exists(get_user_config_file()):
        return load_json(get_user_config_file())
    else:
        print('Setting up Magic Browser')


def get_sync_config_file():
    """
    gets the location of the sync config file.
    :return:
    """
    filepath = get_user_config_file().replace('user_globals.json', 'sync/syncthing.json')
    if os.path.exists(filepath):
        return filepath
    else:
        print('Sync config does not exist: {}'.format(filepath))
        return None


def paths():
    """
    returns paths to all the software used in the cookbook.
    :return:
    """
    return user_config()['paths']


class ProjectConfig(object):
    user_config_file = get_user_config_file()
    user_config = user_config()
    project_config = {}
    shaders_config = {}
    globals_root = None
    master_globals_root = None
    default_files_folder = None
    hdri_folder = None
    cookbook_folder = None
    css_folder = None
    root_folder = None
    hdri_settings_file = None
    project_config_file = None
    shaders_config_file = None
    images_folder = None
    project_management = None
    sync_config_file = get_sync_config_file()

    def __init__(self, path_object=None, company='master', project='master', print_cfg=False):
        self.print_cfg = print_cfg
        self.paths = paths()
        if not path_object:
            self.company = company
            self.project = project
        if path_object:
            self.company = path_object.company
            self.project = path_object.project
        if self.print_cfg:
            print('--------------------------------')
            print('Loading Config for {}: {}'.format(self.company, self.project))
        self.set_globals_path()
        self.get_project_config()
        self.images_folder = os.path.join(self.paths['code_root'], 'resources', 'images')
        self.app_font_folder = os.path.join(self.paths['code_root'], 'resources', 'fonts')
        if self.project_config:
            self.project_management = self.project_config['account_info']['project_management']

    def set_globals_path(self):
        try:
            self.root_folder = self.user_config['paths']['root']
        except KeyError:
            self.root_folder = self.user_config['paths']['root']
        # set self.master_globals_root
        master_globals = os.path.join(self.root_folder, 'master', 'config', 'master', 'globals.json')
        if not os.path.exists(master_globals):
            print('Cant find {}'.format(master_globals))
            return
        # see if we have a company master globals.
        try:
            company_globals = os.path.join(self.root_folder, self.company, 'config', 'master', 'globals.json')
            if os.path.exists(company_globals):
                master_globals = company_globals
        except TypeError:
            pass

        # see if we have project globals.
        try:
            if not self.project:
                project = 'master'
            else:
                project = self.project
            project_globals = os.path.join(self.root_folder, self.company, 'config', project, 'globals.json')
            if os.path.exists(project_globals):
                master_globals = project_globals
        except TypeError:
            pass
        self.project_config_file = master_globals
        self.globals_root = os.path.dirname(master_globals)
        self.css_folder = os.path.join(self.globals_root, 'css')
        self.default_files_folder = os.path.join(self.globals_root, 'default_files')
        self.hdri_folder = os.path.join(self.globals_root, 'hdri')
        self.hdri_settings_file = os.path.join(self.hdri_folder, 'settings.json')
        self.cookbook_folder = os.path.join(self.globals_root, 'cookbook')
        self.shaders_config_file = os.path.join(self.globals_root, 'shaders.json')

    def print_variables(self):
        for elem in self.__dict__:
            print('{}: {}'.format(elem, self.__dict__[elem]))

    def get_user_globals(self):
        # do they have an env variable
        try:

            if os.path.exists(self.user_config_file):
                self.user_config = load_json(self.user_config_file)
        except TypeError:
            print('No cgl_user_globals ENV variable found. Assuming location.')
            if os.path.exists(os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack', 'user_globals.json')):
                self.user_config = load_json(os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack', 'user_globals.json'))
            else:
                print('No Globals Found at %s:' % os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack',
                                                               'user_globals.json'))

    def edit_project_config(self, key_list, value):
        """
        edits the current globals file given a key list and a value.
        :param key_list: list of strings representing a possibly nested key
        :param value:
        :return:
        """
        temp_dict = self.project_config
        last = key_list[-1]
        for each in key_list:
            if each == last:
                temp_dict[each] = value
            temp_dict = temp_dict[each]
        self.save_project_config()

    def edit_user_config(self, key_list, value):
        """

        :param key_list:
        :param value:
        :return:
        """
        temp_dict = self.user_config
        last = key_list[-1]
        for each in key_list:
            if each == last:
                temp_dict[each] = value
            temp_dict = temp_dict[each]
        self.save_user_config()

    def edit_shader_config(self, key_list, value):
        """

        :param key_list:
        :param value:
        :return:
        """
        temp_dict = self.shaders_config
        last = key_list[-1]
        for each in key_list:
            if each == last:
                temp_dict[each] = value
            temp_dict = temp_dict[each]
        self.save_shader_config()

    def save_project_config(self, project_config_dict=None):
        if not project_config_dict:
            project_config_dict = self.project_config
        save_json(self.project_config_file, project_config_dict)

    def save_user_config(self, user_config_dict=None):
        if not user_config_dict:
            user_config_dict = self.user_config
        save_json(self.user_config_file, user_config_dict)

    def save_shader_config(self, shader_config_dict=None):
        if not shader_config_dict:
            shader_config_dict = self.shaders_config
        save_json(self.shader_config_file, shader_config_dict)

    def get_project_config(self):
        """
        returns a dictionary for the current project config globals.
        :return:
        """
        if os.path.exists(self.project_config_file):
            self.project_config = load_json(self.project_config_file)
            return self.project_config
        else:
            print('Project Config {} does not exist,  '.format(self.project_config_file))

    def get_shaders_config(self):
        """
        returns a shader ditionary for use in shading tools.
        :return:
        """
        self.shaders_config = load_json(self.shaders_config_file)
        return self.shaders_config

    def test_string_against_rules(self, test_string, rule, effected_label=None):
        """
        Test for any string to see if it passes any regex "rule" from the global.yaml file.
        :param test_string: string to be tested against regex
        :param rule: regex pattern to test against
        :param effected_label: PySide Label Object to effect color of.
        :return:
        """
        regex = re.compile(r'%s' % self.project_config['rules']['path_variables'][rule]['regex'])
        if re.findall(regex, test_string):
            if effected_label:
                effected_label.setStyleSheet("color: rgb(255, 255, 255);")
            return False
        else:
            if effected_label:
                effected_label.setStyleSheet("color: rgb(255, 50, 50);")
            return self.project_config['rules']['path_variables'][rule]['example']


    def image_path(self, image=None, ):
        """
        get the path where images are stored
        :param image:
        :return:
        """
        if image:
            return os.path.join(self.images_folder, image)
        else:
            return self.images_folder

    def icon_path(self, icon=None):
        """
        get the path where icons are stored.
        :param icon:
        :return:
        """
        if icon:
            return os.path.join(self.paths['code_root'], 'resources', 'icons', icon)
        else:
            return os.path.join(self.paths['code_root'], 'resources', 'icons')

    def font_path(self):
        """
        get the path where fonts for the app are stored
        :return:
        """
        return self.app_font_folder

    def get_cgl_resources_path(self):
        """
        get the resources path
        :return: path string
        """
        return os.path.join(self.paths['code_root'], 'resources')

    def get_task_default_file(self, task):
        """
        returns the path to the default file of the given task
        :param task:
        :return:
        """
        task_folder = os.path.join(self.default_files_folder, task)
        default_file = glob.glob('{}/default.*'.format(task_folder))
        if default_file:
            return os.path.join(task_folder, default_file[0])
        else:
            return None


def copy_config(from_company, from_project, to_company, to_project):
    from_config = ProjectConfig(company=from_company, project=from_project).globals_root
    to_config_root = os.path.join(get_root(from_project), to_company, 'config', to_project)
    print('Copying from {} to {}'.format(from_config, to_config_root))
    cgl_copy(from_config, to_config_root)


def check_for_latest_master(path_object=None):
    from cgl.core.utils.general import cgl_execute
    # TODO - need to look at this and make it require cfg if possible.
    # TODO - probably need something in place to check if git is installed.
    cfg = ProjectConfig(path_object)
    code_root = paths()['code_root']
    command = 'git remote show origin'
    os.chdir(code_root)
    output = cgl_execute(command, return_output=True, print_output=False)['printout']

    for line in output:
        if 'pushes to master' in line:
            if 'up to date' in line:
                print('cglumberjack code base up to date')
                return True
            else:
                print('cglumberjack code base needs updated')
                return False


def update_master(path_object=None, widget=None):
    from cgl.core.utils.general import cgl_execute
    # TODO - need to look at this and make it require cfg if possible.
    cfg = ProjectConfig(path_object)
    code_root = paths()['code_root']
    command = 'git pull'
    os.chdir(code_root)
    cgl_execute(command)
    if widget:
        widget.close()


def get_root(project='master'):
    """
    gets root from the current project defaults to 'master'.
    :return:
    """
    user_conf = user_config()
    return user_conf['paths']['root'].replace('\\', '/')






if __name__ == '__main__':
    print('bob')
    #create_user_globals(root=None)
    # project_config = ProjectConfig(company='bob')
    # print(project_config.globals_root)
    # these return file paths
    # print(project_config.globals_file)
    # print(project_config.shaders_file)
    # print(project_config.user_globals_file)
    # # these return dictionaries for common things
    # print(project_config.user_config)
    # print(project_config.project_config)
    # # this will return a dictionary for the shaders.
    # print(project_config.get_shaders_config())
