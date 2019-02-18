import logging
from plugins.project_management.shotgun.tracking_internal.shotgun_specific import ShotgunQuery
from core.config import app_config


PROJECTSHORTNAME = app_config()['shotgun']['project_short_name']
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
    category = None
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

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

        print 'Creating Entries for Shotgun:'

    def create_project_management_data(self):
        if self.project:
            self.project_data = self.entity_exists('project')
            if not self.project_data:
                self.project_data = self.create_project()
        if self.scope == 'assets':
            if self.category:
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

        if self.entity_data:
            if self.user:
                self.user_data = self.entity_exists('user')
                # TODO - add user to the project if they aren't on it.
                if self.task:
                    # set tas_name
                    if self.scope == 'assets':
                        self.task_name = '%s_%s' % (self.asset, self.task)
                    elif self.scope == 'shots':
                        self.task_name = '%s_%s' % (self.shot, self.task)
                    # get task_data
                    self.task_data = self.entity_exists('task')
                    if not self.task_data:
                        self.task_data = self.create_task()
                    if self.version:
                        if self.scope == 'shots':
                            self.version_name = '%s_%s_%s_%s' % (self.seq, self.shot, self.task, self.version)
                        elif self.scope == 'assets':
                            self.version_name = '%s_%s_%s_%s' % (self.category, self.asset, self.task, self.version)
                        if self.version_name:
                            self.version_data = self.find_version()
                            if not self.version_data:
                                self.version_data = self.create_version()

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
        return data

    def create_version(self):
        data = {'project': self.project_data,
                'entity': self.entity_data,
                'sg_task': self.task,
                'code': self.version_name,
                'user': self.user}
        if self.find_version():
            logging.info('Shotgun Version Already Exists - skipping')
            return
        return ShotgunQuery.create('Version', data)

    def create_project(self, short_name=None):
        if not short_name:
            short_name = self.project
        data = {'name': self.project,
                'sg_code': short_name}
        logging.info('Creating Shotgun Project %s' % self.project)
        return ShotgunQuery.create('Project', data)

    def create_asset(self):
        data = {'project': self.project_data,
                'sg_asset_type': self.category,
                'code': self.asset}
        logging.info('Creating Shotgun Asset %s' % self.asset)
        return ShotgunQuery.create('Asset', data)

    def create_sequence(self):
        data = {'project': self.project_data,
                'code': self.seq}
        return ShotgunQuery.create('Sequence', data)

    def create_shot(self):
        data = {'project': self.project_data,
                'sg_sequence': self.seq_data,
                'code': self.shot}
        return ShotgunQuery.create('Shot', data)

    def create_task(self):
        # Need to catch if this task already exists before attempting to make it.
        # For some reason the "sim" task doesn't work on this, others seem to

        task_data = self.find_task_shortname()
        data = {'project': self.project_data,
                'entity': self.entity_data,
                'step': task_data,
                'task_assignees': [self.user_data],
                'content': self.task_name
                }
        return ShotgunQuery.create('Task', data)

    def find_project(self):
        """

        Returns:

        """
        filters = [['name', 'is', self.project],
                   ]
        return ShotgunQuery.find_one("Project", filters, fields=PROJECTFIELDS)

    def find_asset(self):
        filters = [['code', 'is', self.asset],
                   ['project', 'is', self.project_data],
                   ['sg_asset_type', 'is', self.category]]
        return ShotgunQuery.find_one('Asset', filters, fields=ASSETFIELDS)

    def find_task_shortname(self):
        filters = [['short_name', 'is', self.task]]
        return ShotgunQuery.find_one('Step', filters, fields=STEPFIELDS)

    def find_shot(self):
        filters = [['project', 'is', self.project_data],
                   ['code', 'is', self.seq],
                   ['sg_sequence', 'is', self.seq_data]]
        return ShotgunQuery.find_one('Shot', filters, fields=SHOTFIELDS)

    def find_seq(self):
        filters = [['code', 'is', self.seq],
                   ['project', 'is', self.project_data]]
        return ShotgunQuery.find_one('Sequence', filters, fields=ASSETFIELDS)

    def find_user(self):
        """
        find a user based on object values
        Returns:
            dict: shotgun dict for a HumanUser

        """
        user = ShotgunQuery.find_one('HumanUser',
                                     [['login', 'contains', self.user]],
                                     ['code', 'name', 'id', 'login', 'email', 'projects'])
        return user

    def find_task(self):
        filters = [['project', 'is', self.project_data],
                   ['content', 'is', self.task_name],
                   ['entity', 'is', self.entity_data]
                   ]
        return ShotgunQuery.find("Task", filters, fields=TASKFIELDS)

    def find_version(self):
        filters = [['code', 'is', self.version_name],
                   ['project', 'is', self.project_data]
                   ]
        return ShotgunQuery.find_one("Version", filters, fields=VERSIONFIELDS)

