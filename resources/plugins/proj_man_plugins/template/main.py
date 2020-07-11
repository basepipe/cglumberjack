import logging
import webbrowser
import datetime
import os
import json
from cgl.core.config import app_config

CONFIG = app_config()
PROJECTSHORTNAME = CONFIG['project_management']['shotgun']['api']['project_short_name']
PROJECTFIELDS = ['code', 'name', 'sg_status', 'sg_description', PROJECTSHORTNAME]
HUMANUSERFIELDS = ['code', 'name', 'email', 'department', 'login']
TASKFIELDS = ['content', 'sg_status_list', 'step', 'step.Step.short_name',
              'project.Project.%s' % PROJECTSHORTNAME, 'task_assignees', 'task_assignees.Humanuser.username',
              'name', 'code', 'project', 'project.Project.sg_status', 'project.Project.status',
              'entity', 'entity.Shot.sg_sequence', 'due_date', 'updated_at', 'entity.Asset.sg_asset_type', 'updated_at']
ASSETFIELDS = ['code', 'name', 'status', 'updated_at', 'description']
SHOTFIELDS = ['code', 'sg_sequence', 'status', 'updated_at', 'description']
VERSIONFIELDS = ['code', 'name', 'sg_sequence', 'status', 'updated_at', 'description',
                 'sg_task', 'sg_status_list', 'project', 'versions']
STEPFIELDS = ['code', 'short_name', 'id', ]


class ProjectManagementData(object):
    create = False
    edit = False
    delete = False
    project = None
    task = None
    scope = None
    seq = None
    shot = None
    shot_name = ''
    type = None
    asset = None
    user = None
    time_entry = None
    note = None
    project_data = None
    asset_data = None
    seq_data = None
    shot_data = None
    task_name = None
    task_data = None
    user_data = None
    version = None
    version_name = None
    version_data = None
    entity_data = None
    status = None
    server_url = CONFIG['project_management']['shotgun']['api']['server_url']

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            self.path_object = path_object
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

    def get_project_management_data(self):
        self.project_data = self.entity_exists('project')
        if not self.project_data:
            return
        if self.scope == 'assets':
            if self.type:
                if self.asset:
                    self.asset_data = self.entity_exists('asset')
                    if self.asset_data:
                        self.entity_data = self.asset_data
        elif self.scope == 'shots':
            if self.seq:
                self.seq_data = self.entity_exists('seq')
            if self.shot:
                self.shot_name = '%s_%s' % (self.seq, self.shot)
                self.shot_data = self.entity_exists('shot')
                if self.shot_data:
                    self.entity_data = self.shot_data
        else:
            return

        if self.user:
            self.user_data = self.entity_exists('user')
        if self.entity_data:
            if self.task:
                # set task_name
                if self.scope == 'assets':
                    self.task_name = '%s_%s' % (self.asset, self.task)
                elif self.scope == 'shots':
                    self.task_name = '%s_%s' % (self.shot_name, self.task)
                # get task_data
                self.task_data = self.entity_exists('task')
                if self.version:
                    if self.scope == 'shots':
                        self.version_name = '%s_%s_%s_%s' % (self.seq, self.shot, self.task, self.version)
                    elif self.scope == 'assets':
                        self.version_name = '%s_%s_%s_%s' % (self.type, self.asset, self.task, self.version)
            if self.status:
                self.set_status()

    def create_project_management_data(self):
        print 'im in shotgun land'
        self.project_data = self.entity_exists('project')
        if not self.project_data:
            print 'creating project'
            self.project_data = self.create_project()
        if self.scope == 'assets':
            if self.type:
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
                self.shot_name = '%s_%s' % (self.seq, self.shot)
                self.shot_data = self.entity_exists('shot')
                if not self.shot_data:
                    self.shot_data = self.create_shot()
            self.entity_data = self.shot_data
        else:
            return

        if self.user:
            self.user_data = self.entity_exists('user')
            if self.project_data not in self.user_data['projects']:
                self.add_project_to_user()

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
                if self.version:
                    if self.scope == 'shots':
                        self.version_name = '%s_%s_%s_%s' % (self.seq, self.shot, self.task, self.version)
                    elif self.scope == 'assets':
                        self.version_name = '%s_%s_%s_%s' % (self.type, self.asset, self.task, self.version)
                    if self.version_name:
                        self.version_data = self.find_version()
                        if not self.version_data:
                            self.version_data = self.create_version()
            if self.status:
                self.set_status()
            if self.filename:
                self.create_version()

    def entity_exists(self, data_type):
        """
        See if the entity exists within the project management system. This function is meant to be a wrapper to any
        API we encounter and is meant to keep core code as simple as possible throughout.
        :param data_type:
        :return: data if entity exists, false if it doesn't.
        """
        data = None
        if data_type == 'project':
            data = self.find_project()
        elif data_type == 'asset':
            data = self.find_asset()
        elif data_type == 'seq':
            data = self.find_seq()
        elif data_type == 'shot':
            data = self.find_shot()
        elif data_type == 'user':
            data = self.find_user()
        elif data_type == 'task':
            data = self.find_task()
        elif data_type == 'version':
            print 'found version'
            data = self.create_version()
        return data

    def create_version(self):
        """
        Creates a Version within the Project Management system based off information passed through the PathObject
        :return: Version Data Object
        """
        print 'Do i need to see if the version already exists?'
        if self.filename:
            return self.version_data
        else:
            print('No File Defined, skipping version creation')

    def create_project(self, short_name=None):
        """
        Creates a Project within the Project Management system based off information passed through the PathObject
        :param short_name: Short Name of the Project (typically a linux friendly version of the Project Name)
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

    def upload_media(self):
        """

        :return:
        """
        pass

    def create_review_session(self):
        """

        :return:
        """
        pass

    def add_to_dailies(self):
        """

        :return:
        """
        print 'Adding to Dailies'
        pass

    def add_project_to_user(self):
        """
        Adds Projects to a user's available projects.
        :return:
        """
        pass

    def find_project(self):
        """
        Query to find the project "object" within the Project Management system based off information passed through
        the PathObject
        :return:
        """
        pass

    def find_asset(self):
        """
        Query to find the asset "object" within the Project Management system based off information passed through
        the PathObject
        :return: asset object
        """
        pass

    def find_task_shortname(self):
        """
        Lumbermill often uses shortnames for directories etc... this finds the project short name within the project
        management system.
        :return:
        """
        pass

    def find_shot(self):
        """
        Query to find the shot "object" within the Project Management system based off information passed through
        the PathObject
        :return:
        """
        pass

    def find_seq(self):
        """
        Query to find the sequence within the Project Management system based off information passed through
        the PathObject
        :return:
        """
        pass

    def find_user(self):
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

    def set_status(self, force=False):
        """
        given a data object set the status for it.
        :param data:
        :param status:
        :return:
        """
        pass

    def set_entity_status(self):
        """
        sets status of an entity
        :return:
        """
        pass

    def get_asset_status(self):
        """
        give task name and status name return the status the asset should be.
        :param task:
        :param status:
        :return:
        """
        pass

    def get_status(self):
        """
        get's status for a given task.
        :return:
        """
        pass

    def get_url(self):
        """
        get's the url for whatever PathObject is currently represented.
        :return:
        """
        self.get_project_management_data()
        if self.version:
            return self.get_version_url()
        if self.task:
            print 'task'
            return self.get_task_url()
        if self.shot:
            print 'shot'
            return self.get_shot_url()
        elif self.asset:
            print 'asset not defined yet'
        if self.project:
            print 'project'
            return self.get_proj_url()

    def get_proj_url(self):
        """
        Retrieve the url for a project within the project managemen stystem.
        :return:
        """
        pass

    def get_shot_url(self):
        """
        Retrieve the url for a shot within the project managemen stystem.
        :return:
        """
        pass

    def get_asset_url(self):
        """
        Retrieve the url for a project within the project managemen stystem.
        :return:
        """
        pass

    def get_task_url(self):
        """
        Retrieve the url for a project within the project managemen stystem.
        :return:
        """
        pass

    def get_version_url(self):
        """
        Retrieve the url for a project within the project managemen stystem.
        :return:
        """
        pass

    def go_to_dailies(self, playlist=None):
        """
        Go to the dailies URL that contains the given version.
        :param playlist:
        :return:
        """
        pass




