import logging
import webbrowser
import datetime
import os
import json
from .tracking_internal.shotgun_specific import ShotgunQuery
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
    review_session = None

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
        logging.debug('im in shotgun land')
        self.project_data = self.entity_exists('project')
        if not self.project_data:
            logging.debug('creating project')
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
            logging.debug('found version')
            data = self.create_version()
        return data

    def create_version(self):
        """
        Creates a Version within the Project Management system based off information passed through the PathObject
        :return: Version Data Object
        """
        logging.debug('Do i need to see if the version already exists?')
        if self.filename:
            data = {'project': self.project_data,
                    'entity': self.entity_data,
                    'sg_task': self.task_data,
                    'code': self.version_name,
                    'user': self.user_data}
            logging.debug('Creating Shotgun Version: %s' % self.version)
            self.version_data = ShotgunQuery.create('Version', data)
            self.upload_media()
            logging.debug(self.get_version_url())
            return self.version_data
        else:
            logging.debug('No File Defined, skipping version creation')

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
                'code': self.shot_name}
        logging.info('Creating Shotgun Shot %s' % self.shot_name)
        return ShotgunQuery.create('Shot', data)

    def create_task(self):
        """
        Creates a Task within the Project Management system based off information passed through the PathObject
        :return: task object
        """
        # Need to catch if this task already exists before attempting to make it.
        # For some reason the "sim" task doesn't work on this, others seem to

        task_data = self.find_task_shortname()
        if self.user_data:
            logging.debug('user exists')
            data = {'project': self.project_data,
                    'entity': self.entity_data,
                    'step': task_data,
                    'task_assignees': [self.user_data],
                    'content': self.task_name
                    }
        else:
            logging.debug('no user')
            data = {'project': self.project_data,
                    'entity': self.entity_data,
                    'step': task_data,
                    'content': self.task_name
                    }
        logging.info('Creating Shotgun Task: %s, %s' % (self.task, self.task_name))
        return ShotgunQuery.create('Task', data)

    def upload_media(self):
        """

        :return:
        """
        if not self.file_type:
            logging.debug('Cannot Determine File Type - skipping Shotgun Upload')
            return
        if not os.path.exists(self.path_object.preview_path):
            logging.debug(self.path_object.preview_path, 'Does Not Exist')
            return
        else:
            preview = self.path_object.preview_path
            thumb = self.path_object.thumb_path
        data = {'sg_path_to_frames': self.path_object.path_root,
                'sg_path_to_movie': preview}
        if self.file_type == 'movie' or self.file_type == 'sequence':
            id_ = int(self.version_data['id'])
            ShotgunQuery.upload('Version', id_, preview, field_name='sg_uploaded_movie')
            # ShotgunQuery.upload_thumbnail('Version', id_, thumb)
            # ShotgunQuery.upload('Version', id_, preview, field_name='sg_latest_quicktime')
            ShotgunQuery.update('Version', entity_id=id_, data=data)
            logging.info('movie uploaded to %s' % self.version_data['code'])
        elif self.file_type == 'image':
            ShotgunQuery.upload('Version', self.version_data['id'], preview, 'sg_uploaded_movie')
            ShotgunQuery.update('Version', entity_id=int(self.version_data['id']), data=data)
            logging.info('image uploaded to %s' % self.version_data['code'])
        logging.info('Committing Media to Shotgun')
        self.add_to_dailies()
        # open the web browser

    def create_review_session(self):
        """

        :return:
        """
        #PlaylistDialog is an option we already have if they want to choose which day to send it to.
        playlist_name = 'Dailies %s' % datetime.date.today()
        filters = [['project', 'is', self.project_data], ['code', 'is', playlist_name]]
        play_list = ShotgunQuery.find_one("Playlist", filters, fields=VERSIONFIELDS)
        # filepath = self.path_object.path_root
        append = True
        project = self.project_data
        if play_list:
            versions = play_list['versions']
        else:
            versions = []
        for each in versions:
            if self.version_data['id'] == each['id']:
                append = False
        if append:
            versions.append(self.version_data)
        data = {'project': project,
                'code': playlist_name,
                'versions': versions}
        if play_list:
            logging.info('Adding to Playlist: %s' % playlist_name)
            self.review_session = ShotgunQuery.update('Playlist', play_list['id'], data)
        else:
            logging.info('Creating Playlist: %s' % playlist_name)
            self.review_session = ShotgunQuery.create('Playlist', data)
        pass

    def add_to_dailies(self):
        """

        :return:
        """
        logging.debug('Adding to Dailies')
        if self.version_data:
            print('creating review session')
            self.create_review_session()
            print('going to dailies')
            self.go_to_dailies()
        pass

    def add_project_to_user(self):
        ShotgunQuery.update("HumanUser", self.user_data['id'], {'projects': [self.project_data]},
                            multi_entity_update_modes={'projects': 'add'})

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
                   ['code', 'is', self.shot_name],
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
        return ShotgunQuery.find_one("Task", filters, fields=TASKFIELDS)

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

    def get_frame_range(self):
        """

        :return:
        """
        pass

    def set_frame_range(self):
        """

        :return:
        """
        pass

    def set_status(self, force=False):
        """
        given a data object set the status for it.
        :param data:
        :param status:
        :return:
        """
        if force:
            self.get_project_management_data()
        if self.version_data:
            logging.debug('Setting Version Status to: %s' % self.status)
            ShotgunQuery.update('Version', entity_id=self.version_data['id'], data={'sg_status_list': self.status})
            logging.debug('Setting Task Status to: %s' % self.status)
            ShotgunQuery.update('Task', entity_id=self.task_data['id'], data={'sg_status_list': self.status})
            self.set_entity_status()
            return
        if self.task_data:
            logging.debug('setting status for the task')
            ShotgunQuery.update('Task', entity_id=self.task_data['id'], data={'sg_status_list': self.status})
            self.set_entity_status()

    def set_entity_status(self):
        asset_status = self.get_asset_status()
        logging.debug('Setting Entity Status to: %s' % asset_status)

    def get_asset_status(self):
        """
        give task name and status name return the status the asset should be.
        :param task:
        :param status:
        :return:
        """
        task = self.task
        status = self.status
        keep_same = ['rev', "omt", 'hld', 'not', 'wtg']
        previous_task = ['stdn', 'mdl', 'tex', 'shd']
        long_to_short = {'stdn ip': 's_ip',
                         'stdn pub': 's_pub',
                         'stdn apr': 's_apr',
                         'mdl wtg': 'wtg',
                         'mdl ip': 'm_ip',
                         'mdl pub': 'm_pub',
                         'mdl apr': 'm_apr',
                         'shd ip': 'sh_ip',
                         'shd apr': 'sh_apr',
                         'shd pub': 'sh_pub',
                         'tex ip': 't_ip',
                         'tex apr': 't_apr',
                         'tex pub': 't_pub',
                         'not': 'not',
                         'wtg': 'wtg',
                         'rev': 'rev',
                         'omt': 'omt',
                         'hld': 'hld'
                         }
        if status == 'wtg':
            index = previous_task.index(task)
            if index:
                task = previous_task[index - 1]
                status = 'apr'
                asset_status = '%s %s' % (task, status)
            else:
                asset_status = 'wtg'
        elif status in keep_same:
            asset_status = status
        else:
            asset_status = '%s %s' % (task, status)
        if asset_status in long_to_short.keys():
            return long_to_short[asset_status]
        else:
            logging.debug('Didnt find %s in keys' % asset_status)

    def get_status(self):
        self.project_data = self.entity_exists('project')
        self.find_task()
        if self.task_data:
            data = self.task_data.first()
            return data['status']['name']
            #return self.task_data['status']['name']
        else:
            logging.debug('No Task Data found!')
            return None

    def get_url(self):
        self.get_project_management_data()
        if self.version:
            return self.get_version_url()
        if self.task:
            logging.debug('task')
            return self.get_task_url()
        if self.shot:
            logging.debug('shot')
            return self.get_shot_url()
        elif self.asset:
            logging.debug('asset not defined yet')
        if self.project:
            logging.debug('project')
            return self.get_proj_url()

    def get_proj_url(self):
        return r'%s/page/project_overview?project_id=%s' % (self.server_url, self.project_data['id'])

    def get_shot_url(self):
        return r'%s/detail/Shot/%s' % (self.server_url, str(self.shot_data['id']))

    def get_asset_url(self):
        return r'%s/detail/Asset/%s' % (self.server_url, str(self.asset_data['id']))

    def get_task_url(self):
        return r'%s/detail/Task/%s' % (self.server_url, str(self.task_data['id']))

    def get_version_url(self):
        if self.version_data:
            url = r'%s/detail/Version/%s' % (self.server_url, str(self.version_data['id']))
            return url
        else:
            logging.info('No version found in Shotgun - Submit Review to Create a Version')
            return self.get_task_url()

    def go_to_dailies(self):
        """

        :param playlist_id: ID of the playlist you want.
        :param version:
        :return:
        """
        if self.review_session:
            playlist_url = r'%s/page/review_app_webview?entity_type=Playlist&entity_id=%s' % (self.server_url,
                                                                                              self.review_session['id'])
            webbrowser.open_new_tab(playlist_url)




