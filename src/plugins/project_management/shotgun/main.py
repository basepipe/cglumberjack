import logging
from plugins.project_management.shotgun.tracking_internal.shotgun_specific import ShotgunQuery
from cglcore.config import app_config


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

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

    def create_project_management_data(self):
        self.project_data = self.entity_exists('project')
        if not self.project_data:
            self.project_data = self.create_project()
        if self.scope == 'assets':
            if self.type:
                print 'type = %s' % self.type
                if self.asset:
                    self.asset_data = self.entity_exists('asset')
                    print 'Asset Data:', self.asset_data
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
            print 'No Scope Defined!'
            return

        if self.entity_data:
            if self.task:
                # set task_name
                if self.scope == 'assets':
                    self.task_name = '%s_%s' % (self.asset, self.task)
                elif self.scope == 'shots':
                    self.task_name = '%s_%s' % (self.shot, self.task)
                # get task_data
                self.task_data = self.entity_exists('task')
                print 'TASK DATA FOUND: %s' % self.task_data
                if not self.task_data:
                    self.task_data = self.create_task()
                    print '2 task data: %s' % self.task_data
            if self.user:
                self.user_data = self.entity_exists('user')
                # TODO - add user to the project if they aren't on it.
                if self.version:
                    if self.scope == 'shots':
                        self.version_name = '%s_%s_%s_%s' % (self.seq, self.shot, self.task, self.version)
                    elif self.scope == 'assets':
                        self.version_name = '%s_%s_%s_%s' % (self.type, self.asset, self.task, self.version)
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
            data = self.find_task()[0]
        return data

    def create_version(self):
        """
        Creates a Version within the Project Management system based off information passed through the PathObject
        :return: Version Data Object
        """
        data = {'project': self.project_data,
                'entity': self.entity_data,
                'sg_task': self.task_data,
                'code': self.version_name,
                'user': self.user_data}
        if self.find_version():
            logging.info('Shotgun Version %s Already Exists - skipping' % self.version_name)
            return
        logging.info('Creating Version: %s' % self.version)
        sg_data = ShotgunQuery.create('Version', data)
        return sg_data['id']

    def create_project(self, short_name=None):
        """
        Creates a Project within the Project Management system based off information passed through the PathObject
        :param short_name: Short Name of the Project (typically a linux friendly version of the Project Name)
        :return: project object
        """
        if not short_name:
            short_name = self.project
        data = {'name': self.project,
                'sg_code': short_name}
        logging.info('Creating Shotgun Project %s' % self.project)
        return ShotgunQuery.create('Project', data)

    def create_asset(self):
        """
        Creates a Asset within the Project Management system based off information passed through the PathObject
        :return: asset object
        """
        data = {'project': self.project_data,
                'sg_asset_type': self.type,
                'code': self.asset}
        logging.info('Creating Shotgun Asset %s:%s' % (self.type, self.asset))
        return ShotgunQuery.create('Asset', data)

    def create_sequence(self):
        """
        Creates a sequence within the Project Management system based off information passed through the PathObject
        :return: sequence object
        """
        data = {'project': self.project_data,
                'code': self.seq}
        logging.info('Creating Shotgun Sequence %s' % self.seq)
        return ShotgunQuery.create('Sequence', data)

    def create_shot(self):
        """
        Creates a Shot within the Project Management system based off information passed through the PathObject
        :return: shot object
        """
        data = {'project': self.project_data,
                'sg_sequence': self.seq_data,
                'code': self.shot}
        logging.info('Creating Shotgun Shot %s' % self.shot)
        return ShotgunQuery.create('Shot', data)

    def create_task(self):
        """
        Creates a Task within the Project Management system based off information passed through the PathObject
        :return: task object
        """
        # Need to catch if this task already exists before attempting to make it.
        # For some reason the "sim" task doesn't work on this, others seem to

        task_data = self.find_task_shortname()
        print 'Task Data: %s' % task_data
        print 'User Data: %s' % self.user_data
        if self.user_data:
            data = {'project': self.project_data,
                    'entity': self.entity_data,
                    'step': task_data,
                    'task_assignees': [self.user_data],
                    'content': self.task_name
                    }
        else:
            data = {'project': self.project_data,
                    'entity': self.entity_data,
                    'step': task_data,
                    'content': self.task_name
                    }
        logging.info('Creating Shotgun Task: %s, %s' % (self.task, self.task_name))
        return ShotgunQuery.create('Task', data)

    def find_project(self):
        """
        Query to find the project "object" within the Project Management system based off information passed through
        the PathObject
        :return:
        """
        filters = [['name', 'is', self.project],
                   ]
        return ShotgunQuery.find_one("Project", filters, fields=PROJECTFIELDS)

    def find_asset(self):
        """
        Query to find the asset "object" within the Project Management system based off information passed through
        the PathObject
        :return: asset object
        """
        filters = [['code', 'is', self.asset],
                   ['project', 'is', self.project_data],
                   ['sg_asset_type', 'is', self.type]]
        logging.info('Searching for asset: %s:%s' % (self.type, self.asset))
        return ShotgunQuery.find_one('Asset', filters, fields=ASSETFIELDS)

    def find_task_shortname(self):
        filters = [['short_name', 'is', self.task]]
        return ShotgunQuery.find_one('Step', filters, fields=STEPFIELDS)

    def find_shot(self):
        """
        Query to find the shot "object" within the Project Management system based off information passed through
        the PathObject
        :return:
        """
        filters = [['project', 'is', self.project_data],
                   ['code', 'is', self.seq],
                   ['sg_sequence', 'is', self.seq_data]]
        return ShotgunQuery.find_one('Shot', filters, fields=SHOTFIELDS)

    def find_seq(self):
        """
        Query to find the sequence within the Project Management system based off information passed through
        the PathObject
        :return:
        """
        filters = [['code', 'is', self.seq],
                   ['project', 'is', self.project_data]]
        return ShotgunQuery.find_one('Sequence', filters, fields=ASSETFIELDS)

    def find_user(self):
        """
        Query to find the "user" within the Project Management system based off information passed through
        the PathObject
        :param user:
        :return: user object
        """
        user = ShotgunQuery.find_one('HumanUser',
                                     [['login', 'contains', self.user]],
                                     ['code', 'name', 'id', 'login', 'email', 'projects'])
        return user

    def find_task(self):
        """
        Query to find the "task" within the Project Management system based off information passed through
        the PathObject
        :return: task_object
        """
        filters = [['project', 'is', self.project_data],
                   ['content', 'is', self.task_name],
                   ['entity', 'is', self.entity_data]
                   ]
        return ShotgunQuery.find("Task", filters, fields=TASKFIELDS)

    def find_version(self):
        """
        Query to find the version object within the Project Management system based off information passed through
        the PathObject
        :return: version object
        """
        filters = [['code', 'is', self.version_name],
                   ['project', 'is', self.project_data]
                   ]
        return ShotgunQuery.find_one("Version", filters, fields=VERSIONFIELDS)

