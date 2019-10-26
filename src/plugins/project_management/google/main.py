import logging
import webbrowser
import datetime
import os
import json
import ftrack_api
from cglcore.config import app_config, UserConfig
from cglcore.util import current_user
from cglcore.path import create_previews


class ProjectManagementData(object):
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
    shot_name = '%s_%s' % (seq, shot)
    shot_data = None
    category = None
    asset = None
    user = None
    user_email = None
    user_data = None
    time_entry = None
    note = None
    schema = app_config()['project_management']['ftrack']['api']['default_schema']
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
    preview_path_full = None
    thumb_path_full = None
    task_asset = None
    user_info = app_config()['project_management']['ftrack']['users']
    server_url = app_config()['project_management']['ftrack']['api']['server_url']
    api_key = app_config()['project_management']['ftrack']['api']['api_key']
    api_user = app_config()['project_management']['ftrack']['api']['api_user']
    resolution = 'high'
    auto_close = True

    def __init__(self, path_object=None, session=None, **kwargs):
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
        if not session:
            self.ftrack = ftrack_api.Session(server_url=self.server_url, api_key=self.api_key, api_user=self.api_user)
        else:
            self.ftrack = session
            self.auto_close = False
        self.project_schema = self.ftrack.query('ProjectSchema where name is %s' % self.schema).first()
        # Retrieve default types.
        self.default_shot_status = self.project_schema.get_statuses('Shot')[0]
        self.shot_statuses = self.project_schema.get_statuses('Shot')
        # get the types of tasks for shots.
        if self.task:
            self.task_status_dict = {}
            self.task_types = self.project_schema.get_types('Task')
            self.task_type = self.get_current_task_type()
            self.task_statuses = self.project_schema.get_statuses('Task', self.task_type['id'])
            for i, task in enumerate(self.task_statuses):
                self.task_status_dict[task['name']] = self.task_statuses[i]
            self.default_task_status = self.project_schema.get_statuses('Task', self.task_type['id'])[0]

    def get_current_task_type(self):
        schema = app_config()['project_management']['ftrack']['tasks'][self.schema]
        full_name = schema['short_to_long'][self.scope.lower()][self.task]
        for task in self.task_types:
            if task['name'] == full_name:
                return task
        return None

    def create_project_management_data(self):
        self.project_data = self.entity_exists('project')

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
        pass

    def create_asset(self):
        pass

    def create_sequence(self):
        pass

    def create_shot(self):
        pass

    def create_task(self):
        pass

    def create_assignment(self):
        pass

    def update_user_globals_task(self, status='Not started'):
        # specific to FTRACK?
        pass

    def create_version(self):
        pass

    def upload_media(self):
        pass

    def create_review_session(self):
        pass

    def add_to_dailies(self):
        pass

    def add_group_to_project(self):
        pass

    def find_task_asset(self):
        pass

    def find_group_on_project(self):
        pass

    def add_user_to_project(self):
        pass

    def find_project(self):
        self.project_data = None
        return False

    def find_shot(self):
        self.shot_data = None
        return self.shot_data

    def find_seq(self):
        self.seq_data = None
        return self.seq_data

    def find_project_team(self):
        self.project_team = None
        return self.project_team

    def find_user(self, user=None):
        self.user_data = None
        return self.user_data

    def find_task(self):
        self.task_data = None
        return self.task_data

    def find_version(self):
        self.version_data = None
        return self.version_data

    def get_status(self):
        pass

    def get_url(self):
        """
        returns url based off current path
        :return:
        """
        pass

    def get_proj_url(self, project):
        project_url = ''
        return project_url

    def get_shot_url(self, project, seq, shot):
        """
        returns the url for the shot in the path_object.
        :param project:
        :param seq:
        :param shot:
        :return:
        """
        url = ''
        return url

    def get_task_url(self, project, seq, shot, task, view):
        url = ''
        return url

    def get_version_url(self, show_qt=True):
        pass

    def go_to_dailies(self, playlist=None):
        pass


def find_user_assignments(path_object, user_email, force=False):
    pass

