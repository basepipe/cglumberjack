import logging
import webbrowser
import datetime
import os
import json
import ftrack_api
from cglcore.config import app_config


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
    type = None
    thumb_path_full = None
    preview_path_full = None
    task_asset = None
    server_url = app_config()['project_management']['ftrack']['api']['server_url']
    api_key = app_config()['project_management']['ftrack']['api']['api_key']
    api_user = app_config()['project_management']['ftrack']['api']['api_user']
    resolution = 'high'

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            self.path_object = path_object
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]
        self.shot_name = '%s_%s' % (self.seq, self.shot)
        if not self.user_email:
            self.user_email = app_config()['project_management']['ftrack']['api']['api_user']
            if not self.user_email:
                logging.debug('No User Email Defined, cant create Ftrack Production Data')
                return
        else:
            print 'User email pre-set %s' % self.user_email

        if not self.project:
            logging.debug('No Project Defined')
            return

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

        self.ftrack = ftrack_api.Session(server_url=self.server_url, api_key=self.api_key, api_user=self.api_user)
        self.project_schema = self.ftrack.query('ProjectSchema where name is %s' % self.schema).first()
        # Retrieve default types.
        self.default_shot_status = self.project_schema.get_statuses('Shot')[0]
        self.shot_statuses = self.project_schema.get_statuses('Shot')
        # get the types of tasks for shots.
        if self.task:
            self.task_types = self.project_schema.get_types('Task')
            self.task_type = self.get_current_task_type()
            self.task_statuses = self.project_schema.get_statuses('Task', self.task_type['id'])
            self.default_task_status = self.project_schema.get_statuses('Task', self.task_type['id'])[0]

    def get_current_task_type(self):
        schema = app_config()['project_management']['ftrack']['tasks'][self.schema]
        full_name = schema['short_to_long'][self.scope.lower()][self.task]
        for task in self.task_types:
            if task['name'] == full_name:
                return task
        logging.debug('Could Not Find a Task of %s' % task['name'])
        return None

    def create_project_management_data(self, review=False):
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
            if self.version:
                self.create_version()
            if review:
                self.upload_media()
            elif self.filename:
                self.create_component()
        self.ftrack.commit()
        self.ftrack.close()

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
        try:
            if data_:
                logging.debug('Found %s: %s, No Need to Create' % (data_type, data_['name']))
            return data_
        except:
            logging.debug('Did not find %s' % data_type)
            return None

    def create_project(self):
        logging.info('Creating Ftrack Project %s' % self.project)
        project = self.ftrack.create('Project', {
            'name': self.project_short_name,
            'full_name': self.project,
            'project_schema': self.project_schema
        })
        return project

    def create_asset(self):
        logging.info('Creating FTRACK Asset %s' % self.asset)
        self.asset_data = self.ftrack.create('AssetBuild', {
            'name': self.asset,
            'parent': self.project_data
        })
        return self.asset_data

    def create_sequence(self):
        logging.info('Creating FTRACK Sequence %s' % self.seq)
        self.seq_data = self.ftrack.create('Sequence', {
            'name': self.seq,
            'parent': self.project_data
        })
        return self.seq_data

    def create_shot(self):
        self.shot_name = '%s_%s' % (self.seq, self.shot)
        logging.info("Creating FTRACK Shot %s" % self.shot_name)
        self.shot_data = self.ftrack.create('Shot', {
            'name': self.shot_name,
            'parent': self.seq_data,
            'status': self.default_shot_status
        })
        return self.shot_data

    def create_task(self):
        logging.info('Creating FTRACK Task %s, %s' % (self.task_name, self.task_type['name']))
        self.task_data = self.ftrack.create('Task', {
            'name': self.task_name,
            'parent': self.entity_data,
            'status': self.default_task_status,
            'type': self.task_type
        })
        if self.thumb_path_full:
            if os.path.exists(self.thumb_path_full):
                logging.debug(self.thumb_path_full)
                self.task_data.create_thumbnail(self.thumb_path_full)
        return self.task_data

    def create_assignment(self):
        logging.debug('Checking for Assignment %s' % self.task_data['name'])
        existing_assignment = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="assignment"'.format(
                self.task_data['id'], self.user_data['id'])).first()
        if not existing_assignment:
            logging.info('Creating FTRACK Assignment %s: for %s' % (self.task, self.user_email))
            self.assignment_data = self.ftrack.create('Appointment', {
                'context': self.task_data,
                'resource': self.user_data,
                'type': 'assignment'
            })
            return self.assignment_data
        else:
            return None

    def create_version(self):
        try:
            self.ftrack.event_hub.connect()
        except:
            pass
        # first we'll create an AssetType - for now we're calling everything an "upload" lack of a better plan.
        asset_type = self.ftrack.query('AssetType where name is "%s"' % self.ftrack_asset_type).first()

        self.task_asset = self.find_task_asset()
        if not self.task_asset:
            self.task_asset = self.ftrack.create('Asset', {
                'name': self.version,
                'type': asset_type,
                'parent': self.entity_data
            })

        self.version_data = self.find_version()
        if not self.version_data:
            self.version_data = self.ftrack.create('AssetVersion', {
                'asset': self.task_asset,
                'task': self.task_data
            })
            logging.info('Creating FTRACK Version %s for: %s' % (self.version, self.task_name))
        else:
            logging.debug('Found %s, No Need to Create' % self.version)
        return self.version_data

    def create_component(self):
        from cglcore.path import lj_list_dir, prep_seq_delimiter

        # format to ftrack specs: {head}{padding}{tail} [{ranges}] eg: /path/to/file.%04d.ext [1-5, 7, 8, 10-20]
        if self.path_object.filename != '*.':
            if self.path_object.file_type:
                if self.path_object.file_type == 'sequence':
                    seq = os.path.dirname(self.path_root)
                    sequence = lj_list_dir(seq, return_sequences=True)
                    seq2, frange = sequence[0].split()
                    path = os.path.join(seq, seq2)
                    ftrack_path = '%s [%s]' % (prep_seq_delimiter(path, '%'), frange)
                    logging.info('Creating FTRACK Component for %s' % ftrack_path)
                    self.version_data.create_component(path=ftrack_path, data={'name': self.resolution})
                else:
                    print 'FTRACK components not prepared for %s' % self.path_object.file_type

    def upload_media(self):
        if os.path.exists(self.preview_path_full):
            server_location = self.ftrack.query('Location where name is "ftrack.server"').first()
            if self.file_type == 'movie' or self.file_type == 'sequence':
                component = self.version_data.create_component(
                    path=self.preview_path_full,
                    data={
                        'name': 'ftrackreview-mp4'
                    },
                    location=server_location
                )
                # self.version_data.encode_media(component)
                component['metadata']['ftr_meta'] = json.dumps({
                    'frameIn': 0,
                    'frameOut': 150,
                    'frameRate': 25
                })
                thumb_component = self.version_data.create_component(
                    path=self.path_object.thumb_path_full,
                    data={'name': 'thumbnail'},
                    location=server_location
                )

            elif self.file_type == 'image':
                component = self.version_data.create_component(
                    path=self.path_object.preview_path_full,
                    data={
                        'name': 'ftrackreview-image'
                    },
                    location=server_location
                )
                component['metadata']['ftr_meta'] = json.dumps({
                    'format': 'image'
                })
                thumb_component = self.version_data.create_component(
                                  path=self.path_object.thumb_path_full,
                                  data={'name': 'thumbnail'},
                                  location=server_location
                )
            self.version_data['thumbnail'] = thumb_component
            logging.info('Committing Media')
            component.session.commit()
            thumb_component.session.commit()
            self.add_to_dailies()
        else:
            logging.info('No Preview Image or Movie found to upload! %s' % self.preview_path_full)

    def create_review_session(self):
        self.ftrack.create('ReviewSession', {
            'name': 'Dailies %s' % datetime.date.today(),
            'description': 'Review Session For Todays Data',
            'project': self.project_data
        })

    def add_to_dailies(self):
        list_name = 'Dailies: %s' % datetime.date.today()
        # TODO - this is likely just for loneCoconut at the moment.
        list_category = self.ftrack.query('ListCategory where id is %s' %
                                          '77b9ab82-07c2-11e4-ba66-04011030cf01').first()
        version_list = self.ftrack.query('AssetVersionList where name is "%s" and project.id is "%s"'
                                         % (list_name, self.project_data['id'])).first()
        if not version_list:
            version_list = self.ftrack.create('AssetVersionList', {
                'name': list_name,
                'owner': self.user_data,
                'project': self.project_data,
                'category': list_category
            })
            logging.info('Adding FTRACK version %s to %s' % (self.version_data['id'], list_name))
            if self.version_data not in version_list['items']:
                version_list['items'].append(self.version_data)
        else:
            logging.info('Adding FTRACK version %s to %s' % (self.version_data['id'], list_name))
            if self.version_data not in version_list['items']:
                version_list['items'].append(self.version_data)

        self.go_to_dailies(playlist=version_list['id'])

    def add_group_to_project(self):
        self.user_group = self.ftrack.query('Group where name is %s' % self.user_group_name)[0]
        self.user_data = self.ftrack.query('User where username is "{}"'.format(self.user_email)).one()
        self.ftrack.ensure('Membership', {"group_id": self.user_group['id'], "user_id": self.user_data['id']})
        project_has_group = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="allocation"'.format(
                self.project_data['id'], self.user_group['id']
            )
        ).first()

        if not project_has_group:
            logging.info('Assigning group {} to project {}'.format(self.user_group['name'], self.project_data['name']))
            self.ftrack.create('Appointment', {
                'context': self.project_data,
                'resource': self.user_group,
                'type': 'allocation'
            })
        else:
            logging.debug('Group {} already in assigned to project {}'.format(self.user_group['name'],
                                                                              self.project_data['name']))

    def find_task_asset(self):
        task_asset = self.ftrack.query('Asset where name is "{0}" and '
                                       'parent.id is "{1}"'.format(self.version, self.entity_data['id']))
        if len(task_asset) > 0:
            return task_asset[0]
        else:
            return task_asset

    def find_group_on_project(self):
        project_has_group = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="allocation"'.format(
                self.project_data['id'], self.user_group['id']
            )
        ).first()
        return project_has_group

    def add_user_to_project(self):
        project_has_user = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="allocation"'.format(
                self.project_data['id'], self.user_data['id']
            )
        ).first()

        if not project_has_user:
            logging.info('Assigning user {} to project {}'.format(self.user_data['username'],
                                                                  self.project_data['name']))
            self.ftrack.create('Appointment', {
                'context': self.project_data,
                'resource': self.user_data,
                'type': 'allocation'
            })

        else:
            logging.debug('User {} already in assigned to project {}'.format(self.user_data['username'],
                                                                            self.project_data['name']))

    def find_project(self):
        self.project_data = self.ftrack.query('Project where status is active and name is %s' %
                                              self.project_short_name).first()
        if self.project_data:
            return self.project_data
        else:
            logging.debug('%s Not Found' % self.project)
            return False

    def find_asset_build(self):
        asset = self.ftrack.query('AssetBuild where '
                                  'name is "%s" and project.id is "%s"' % (self.asset, self.project_data['id'])).first()
        if asset:
            self.asset_data = asset
            return self.asset_data
        else:
            return self.create_asset()

    def find_shot(self):
        self.shot_data = self.ftrack.query('Shot where name is %s and project.id is %s' %
                                           (self.shot_name, self.project_data['id'])).first()
        return self.shot_data

    def find_seq(self):
        seqs = self.ftrack.query('Sequence where name is "{0}" '
                                 'and project.id is "{1}"'.format(self.seq, self.project_data['id'])).first()
        return seqs

    def find_project_team(self):
        self.project_team = set()
        for allocation in self.project_data['allocations']:
            resource = allocation['resource']

            if isinstance(resource, self.ftrack.types['Group']):
                for membership in resource['memberships']:
                    user = membership['user']
                    self.project_team.add(user)

    def find_user(self):
        if not self.user_data:
            self.user_data = self.ftrack.query('User where username is "{}"'.format(self.user_email)).first()
        self.add_user_to_project()
        return self.user_data

    def find_task(self):
        self.task_data = self.ftrack.query('Task where name is "{0}" '
                                           'and project.id is "{1}"'.format(self.task_name, self.project_data['id']))
        return self.task_data

    def find_version(self):
        self.version_data = self.ftrack.query('AssetVersion where asset_id is %s' % self.task_asset['id']).first()
        return self.version_data

    def get_proj_url(self, project):
        project = self.ftrack.query('Project where status is active and name is %s' % project).first()
        start_string = "https://lone-coconut.ftrackapp.com/#entityId=%s&entityType=" \
                       "show&itemId=projects&view=tasks" % project['id']
        return start_string

    def get_shot_url(self, project, seq, shot):
        """
        returns the url for the shot in the path_object.
        :param project:
        :param seq:
        :param shot:
        :return:
        """
        shot = self.ftrack.query('Shot where name is %s_%s and project.name is %s' % (seq, shot, project)).first()
        start_string = 'https://lone-coconut.ftrackapp.com/#entityId=%s&entityType=' \
                       'task&itemId=projects&view=tasks' % shot['id']
        return start_string

    def get_task_url(self, project, seq, shot, task, view):
        # TODO - change this to work with the local variables

        if view == 'seq':
            scope = self.ftrack.query('Sequence where name is %s and project.name is %s' % (seq, project)).first()
            scope_id = scope['id']
            task = self.ftrack.query(
                'Task where name is %s_%s_%s and project.name is %s' % (seq, shot, task, project)).first()
            task_string = 'https://lone-coconut.ftrackapp.com/#slideEntityId=%s&slideEntityType=task&view=' \
                          'tasks&itemId=projects&entityId=%s&entityType=task' % (task['id'], scope_id)
        elif view == 'shot':
            scope = self.ftrack.query('Shot where name is %s_%s and project.name is %s' % (seq, shot, project)).first()
            scope_id = scope['id']
            task = self.ftrack.query(
                'Task where name is %s_%s_%s and project.name is %s' % (seq, shot, task, project)).first()
            task_string = 'https://lone-coconut.ftrackapp.com/#slideEntityId=%s&slideEntityType=' \
                          'task&view=tasks&itemId=projects&entityId=%s&entityType=task' % (task['id'], scope_id)
        elif view == 'project':
            scope = self.ftrack.query('Project where name is %s' % project).first()
            scope_id = scope['id']
            task = self.ftrack.query('Task where name is %s_%s_%s and '
                                     'project.name is %s' % (seq, shot, task, project)).first()
            task_string = 'https://lone-coconut.ftrackapp.com/#slideEntityId=%s&slideEntityType=' \
                          'task&view=tasks&itemId=projects&entityId=%s&entityType=show' % (task['id'], scope_id)

        return task_string

    def get_version_url(self, show_qt=True):
        pass

    def go_to_dailies(self, playlist=None):
        if not playlist:
            list_name = 'Dailies: %s' % datetime.date.today()
            version_list = self.ftrack.query('AssetVersionList where name is "%s" and project.id is "%s"'
                                             % (list_name, self.project_data['id'])).first()
            playlist = version_list['id']
        url_string = r'%s/widget/#view=freview_webplayer_v1&itemId=freview&entityType=list&entityId=' \
                     r'%s&controller=widget' % (self.server_url, playlist)
        webbrowser.open(url_string)
        print url_string


if __name__ == "__main__":
    this = ProjectManagementData()
    this.create_project_management_data()
    this.ftrack.commit()
    #this.upload_media()



