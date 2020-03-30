import logging
# import webbrowser
# import datetime
# import os
# import json
from cgl.core.config import app_config, UserConfig
from core.utils.general import current_user
# from cgl.core.path import create_previews

CONFIG = app_config()


class ProjectManagementData(object):
    """
    This is intended to be used as a template for creating API connections to
    just about any project management system.  Once everything is filled out
    we should have a working version of project management fo just about anything.
    """
    project_management = 'lumbermill'
    create = False
    edit = False
    delete = False
    project = None
    project_short_name = None
    project_data = None
    task = None
    task_data = None
    seq = None
    seq_data = None
    shot = None
    shot_data = None
    category = None
    asset = None
    user = None
    user_email = None
    user_data = None
    time_entry = None
    note = None
    schema_data = None
    version = None
    version_data = None
    entity_data = None
    asset_data = None
    scope = None
    context = None
    task_name = None
    project_team = None
    assignments = []
    assignment_data = None
    user_group_name = 'All'
    user_group = None
    appointment = None
    path_root = None
    file_type = None
    filename = None
    ext = None
    ftrack_asset_type = 'Upload'
    description = ''
    bid = 0
    type = None
    preview_path = None
    thumb_path = None
    task_asset = None
    task_status_dict = {}
    task_types = []
    task_type = None
    task_statuses = None
    default_task_status = ''
    resolution = 'high'
    auto_close = True

    def __init__(self, path_object=None, session=None, **kwargs):
        self.user_info = CONFIG['project_management'][self.project_management]['users']
        self.schema = CONFIG['project_management'][self.project_management]['api']['default_schema']
        self.server_url = CONFIG['project_management'][self.project_management]['api']['server_url']
        self.api_key = CONFIG['project_management'][self.project_management]['api']['api_key']
        self.api_user = CONFIG['project_management'][self.project_management]['api']['api_user']
        if path_object:
            self.path_object = path_object
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]
        self.shot_name = '%s_%s' % (self.seq, self.shot)
        if not self.project_short_name:
            self.project_short_name = self.project

        if self.shot == '*':
            self.shot = None
        if self.asset == '*':
            self.asset = None
        if self.seq == '*':
            self.seq = None
        if self.type == '*':
            self.type = None
        if self.user == '*':
            self.user = None
        if self.task == '*':
            self.task = None
        if self.task:
            if self.scope == 'assets':
                self.task_name = '%s_%s' % (self.asset, self.task)
            elif self.scope == 'shots':
                self.task_name = '%s_%s' % (self.shot_name, self.task)
        self.session = self.set_session(session=session)
        self.set_status_variables()
        # Retrieve default types.
        # get the types of tasks for shots.

    def set_status_variables(self):
        """
        Goes through the dictionary of statuses within the globals and sets the following variables:
        self.task_status_dict
        self.task_types
        self.task_statuses
        self.default_task_status
        for working
        with statuses throughout this module.
        :return:
        """
        if self.task:
            self.task_status_dict = {}
            self.task_types = self.project_schema.get_types('Task')
            self.task_type = self.get_current_task_type()
            self.task_statuses = self.project_schema.get_statuses('Task', self.task_type['id'])
            for i, task in enumerate(self.task_statuses):
                self.task_status_dict[task['name']] = self.task_statuses[i]
            self.default_task_status = self.project_schema.get_statuses('Task', self.task_type['id'])[0]
            
    def set_session(self, session):
        """

        :param self:
        :param session:
        :return: active API session
        """
        # if not session:
        #     session = # create API call here
        # else:
        #     self.session = session
        self.session = session
        return self.session

    def get_current_task_type(self):
        schema = CONFIG['project_management']['ftrack']['tasks'][self.schema]
        full_name = schema['short_to_long'][self.scope.lower()][self.task]
        for task in self.task_types:
            if task['name'] == full_name:
                return task
        return None

    def create_project_management_data(self):
        """
        Creates All necessary project management data according to what is given to us within the PathObject.
        :return: 
        """
        self.project_data = self.entity_exists('project')
        if not self.project_data:
            if self.project:
                self.project_data = self.create_project()
            else:
                logging.debug('No Project Defined, Skipping Project creation')
                return
        if not self.user_group:
            self.add_group_to_project()
        if self.scope == 'assets':
            if self.asset:
                self.asset_data = self.entity_exists('asset')
                if not self.asset_data:
                    self.asset_data = self.create_asset()
                self.entity_data = self.asset_data
        elif self.scope == 'shots':
            if self.seq:
                self.seq_data = self.entity_exists('seq')
                if not self.seq_data:
                    self.seq_data = self.create_sequence()
            if self.shot:
                self.shot_data = self.entity_exists('shot')
                if not self.shot_data:
                    self.shot_data = self.create_shot()
                self.entity_data = self.shot_data
        else:
            logging.info('No Scope Defined!')
        if self.entity_data:
            if self.task:
                # set task_name
                if self.scope == 'assets':
                    self.task_name = '%s_%s' % (self.asset, self.task)
                elif self.scope == 'shots':
                    self.task_name = '%s_%s' % (self.shot_name, self.task)
                # get task_data
                self.task_data = self.entity_exists('task')
                if not self.task_data:
                    self.task_data = self.create_task()
                if self.user_email:
                    self.entity_exists('user')
                    if self.user_data:
                        if self.entity_data:
                            self.create_assignment()
            if self.filename:
                self.create_version()

        if self.auto_close:
            self.session.commit()
            self.session.close()

    def entity_exists(self, data_type):
        """
        See if the entity exists within the project management system. This function is meant to be a wrapper to any
        API we encounter and is meant to keep core code as simple as possible throughout.
        :param data_type:
        :return: data if entity exists, false if it doesn't.
        """
        data_ = None
        if data_type == 'project':
            data_ = self.find_project()
        elif data_type == 'asset':
            data_ = self.find_asset_build()
        elif data_type == 'seq':
            data_ = self.find_seq()
        elif data_type == 'shot':
            data_ = self.find_shot()
        elif data_type == 'user':
            data_ = self.find_user()
        elif data_type == 'task':
            data_ = self.find_task()
            if data_:
                data_ = data_[0]
        elif data_type == 'version':
            data_ = self.create_version()
        return data_

    def create_project(self):
        """
        Creates a Project within the Project Management system based off information passed through the PathObject
        :return: project object
        """
        pass

    def create_asset(self):
        """
        Creates a Asset within the Project Management system based off information passed through the PathObject
        :return: asset object
        """
        pass

    def create_sequence(self):
        """
        Creates a sequence within the Project Management system based off information passed through the PathObject
        :return: sequence object
        """
        pass

    def create_shot(self):
        """
        Creates a Shot within the Project Management system based off information passed through the PathObject
        :return: shot object
        """
        pass

    def create_task(self):
        """
        Creates a Task within the Project Management system based off information passed through the PathObject
        :return: task object
        """
        pass

    def create_assignment(self):
        """
        Create's an assignment within the Project Management system based off information passed through the PathObject
        :return: Assignment Object
        """
        pass

    def update_user_globals_task(self, status='Not started'):
        """
        Updates the User Globals File within within the Project Management system based off information passed 
        through the PathObject
        :param status: 
        :return: 
        """
        if self.user_info[current_user()]['login'] == self.user_email:
            my_tasks = UserConfig().d['my_tasks']
            if self.path_object.company not in my_tasks:
                my_tasks[self.path_object.company] = {}
            if self.path_object.project not in my_tasks[self.path_object.company]:
                print 'didnt find %s' % self.path_object.project
                my_tasks[self.path_object.company][self.path_object.project] = {}
            else:
                print my_tasks[self.path_object.company][self.path_object.project]
            new_path = self.path_root.split(self.user)[0]
            my_tasks[self.path_object.company][self.path_object.project][self.task_name] = {}
            task_info = my_tasks[self.path_object.company][self.path_object.project][self.task_name]
            task_info['seq'] = self.seq
            task_info['shot_name'] = self.shot_name
            task_info['bid'] = self.bid
            task_info['due_date'] = ''
            task_info['filepath'] = new_path
            task_info['task_type'] = self.task
            task_info['status'] = status
            UserConfig(my_tasks=my_tasks).update_all()

    def create_version(self):
        """
        Creates a Version within the Project Management system based off information passed through the PathObject
        :return: Version Data Object 
        """
        return self.version_data

    def upload_media(self):
        """
        uploads the media in within the Project Management system based off information passed through the PathObject
        :return: URL for uploaded Media
        """
        pass
        
    def find_user_group(self):
        """
        Some Project Management tools require user 'groups' for projects this is a function that allows for that 
        possibility.
        :return: Group Data Object
        """
        pass

    def add_user_group_to_project(self, group_name):
        """
        Adds user group to the Project Management system
        :return: 
        """
        pass

    def add_user_to_project(self):
        """
        adds User within the Project Management system based off information passed through the PathObject
        :return: User Data Object.
        """
        pass

    def find_project(self):
        """
        Query to find the project "object" within the Project Management system based off information passed through 
        the PathObject
        :return: 
        """
        self.project_data = None
        return self.project_data
        
    def find_asset(self):
        """
        Query to find the asset "object" within the Project Management system based off information passed through 
        the PathObject
        :return: asset object
        """
        self.asset_data = None
        return self.asset_data

    def find_shot(self):
        """
        Query to find the shot "object" within the Project Management system based off information passed through 
        the PathObject
        :return: 
        """
        self.shot_data = None
        return self.shot_data

    def find_seq(self):
        """
        Query to find the sequence within the Project Management system based off information passed through 
        the PathObject
        :return: 
        """
        seqs = None
        return seqs

    def find_project_group(self):
        """
        Query to find the "team" within the Project Management system based off information passed through 
        the PathObject
        :return: team object
        """
        pass

    def find_user(self, user=None):
        """
        Query to find the "user" within the Project Management system based off information passed through 
        the PathObject
        :param user: 
        :return: user object
        """
        pass

    def find_task(self):
        """
        Query to find the "task" within the Project Management system based off information passed through 
        the PathObject
        :return: task_object
        """
        pass

    def find_version(self):
        """
        Query to find the version object within the Project Management system based off information passed through 
        the PathObject
        :return: version object
        """
        pass

    def get_status(self, kind='task'):
        """
        Query to find the status of a given task, asset, or version within the project management system based off 
        information passed through the PathObject.
        :return: status
        """
        pass

    def get_url(self):
        """
        Query to find the URL within the Project Management system based off information passed through 
        the PathObject
        :return: URL
        """
        pass

    def get_proj_url(self, project):
        """
        Query to find specifically the project URL within the Project Management system based off information passed through 
        the PathObject
        :param project: 
        :return: project URL
        """

    def get_shot_url(self, project, seq, shot):
        """
        returns the url for the shot in the path_object.
        :param project:
        :param seq:
        :param shot:
        :return: shot url
        """
        pass

    def get_task_url(self, project, seq, shot, task, view):
        """
        specifically returns the task_url given the current PathObject
        :param project: 
        :param seq: 
        :param shot: 
        :param task: 
        :param view: 
        :return: URL
        """
        pass

    def get_version_url(self, show_qt=True):
        """
        get the url of the version represented by the PathObject
        :param show_qt: 
        :return: URL
        """
        pass

    def get_playlist_url(self, playlist_name=None):
        """
        Get the URL for a given playlist name.
        :param playlist: 
        :return: URL string
        """
        pass


def find_user_assignments(path_object, user_email, force=False):
    from cgl.core.path import PathObject
    continue_parse = False
    company = path_object.company
    project = path_object.project
    # load whatever is in the user globals:
    if company and project and company != '*' and project != '*':
        my_tasks = UserConfig().d['my_tasks']
        if not force:
            try:
                return my_tasks[company][project]
            except KeyError:
                continue_parse = True
        else:
            continue_parse = True
        if continue_parse:
            print 'GATHERING TASK DATA FROM FTRACK'
            server_url = CONFIG['project_management']['ftrack']['api']['server_url']
            api_key = CONFIG['project_management']['ftrack']['api']['api_key']
            api_user = CONFIG['project_management']['ftrack']['api']['api_user']
            schema = CONFIG['project_management']['ftrack']['api']['default_schema']
            long_to_short = CONFIG['project_management']['ftrack']['tasks'][schema]['long_to_short']
            session = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)
            project_name = project
            user = user_email
            project_data = session.query('Project where status is active and name is %s' % project_name).first()
            if project_data:
                user_data = session.query('User where username is "{}"'.format(user)).first()
                project_tasks = session.query('select name, type.name, parent.name, status.name, '
                                              'assignments.resource from Task where project.id is %s' % project_data['id'])
                if not my_tasks:
                    my_tasks = {company: {project: {}}}
                else:
                    my_tasks[company][project] = {}
                for p in project_tasks:
                    seq = ''
                    shot_ = ''
                    for i, _ in enumerate(p['assignments']):
                        if p['assignments'][i]['resource'] == user_data:
                            if 'AssetBuild' in str(type(p['parent'])):
                                scope = 'assets'
                                seq = 'prop'  # TODO This is not stable at the moment. Category for Assets isn't a thing
                                shot_ = p['parent']['name']
                            else:
                                if '_' in p['parent']['name']:
                                    seq, shot_ = p['parent']['name'].split('_')
                                scope = 'shots'
                            task_type = long_to_short[scope][p['type']['name']]
                            my_tasks[company][project][p['name']] = {}
                            name_ = my_tasks[company][project][p['name']]
                            name_['seq'] = seq
                            name_['shot_name'] = p['parent']['name']
                            name_['filepath'] = PathObject(path_object).copy(scope=scope, seq=seq, shot=shot_,
                                                                             task=task_type).path_root
                            my_tasks[company][project][p['name']]['task_type'] = task_type
                            my_tasks[company][project][p['name']]['status'] = p['status']['name']
                            my_tasks[company][project][p['name']]['due_date'] = ''
                session.close()
                UserConfig(my_tasks=my_tasks).update_all()
                return my_tasks[company][project]
            else:
                return None
    else:
        print 'Invalid Input Value(s): Company = %s, Project = %s' % (company, project)


if __name__ == "__main__":
    this = ProjectManagementData()
    this.create_project_management_data()
    this.ftrack.commit()


