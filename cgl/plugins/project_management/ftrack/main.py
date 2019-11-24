import logging
import webbrowser
import datetime
import os
import json
import ftrack_api
from cgl.core.config import app_config, UserConfig
from cgl.core.util import current_user


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
    preview_path = None
    thumb_path = None
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
        return data_

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
            'status': self.default_shot_status,
            'description': self.description
        })
        return self.shot_data

    def create_task(self):
        logging.info('Creating FTRACK Task %s, %s' % (self.task_name, self.task_type['name']))
        self.task_data = self.ftrack.create('Task', {
            'name': self.task_name,
            'parent': self.entity_data,
            'status': self.default_task_status,
            'type': self.task_type,
            'description': self.description,
            'bid': self.bid
        })
        if self.thumb_path:
            if os.path.exists(self.thumb_path):
                logging.debug(self.thumb_path)
                self.task_data.create_thumbnail(self.thumb_path)
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
            self.update_user_globals_task()
            return self.assignment_data
        else:
            return None

    def update_user_globals_task(self, status='Not started'):
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
        if self.filename:
            # first we'll create an AssetType - for now we're calling everything an "upload" lack of a better plan.
            asset_type = self.ftrack.query('AssetType where name is "%s"' % self.ftrack_asset_type).first()

            self.task_asset = self.find_task_asset()
            if not self.task_asset:
                self.task_asset = self.ftrack.create('Asset', {
                    'name': self.task,
                    'type': asset_type,
                    'parent': self.entity_data
                })
            self.version_data = self.ftrack.create('AssetVersion', {
                'asset': self.task_asset,
                'task': self.task_data,
            })
            self.upload_media()
            #     logging.info('Creating FTRACK Version %s for: %s' % (self.version, self.task_name))
            # else:
            #     logging.debug('Found %s, No Need to Create' % self.version)
        else:
            print('No File defined, skipping version creation')
        return self.version_data

    def upload_media(self, force_creation=False):
        # set the status name to 'Needs Review'
        if not self.file_type:
            print 'Cannot Determine File Type - skipping Ftrack Upload'
            return
        if not os.path.exists(self.path_object.preview_path):
            print self.path_object.preview_path, 'Does Not Exist'
            return

        else:
            preview = self.path_object.preview_path
            thumb = self.path_object.thumb_path
        server_location = self.ftrack.query('Location where name is "ftrack.server"').first()
        thumb_component = ''
        component = None
        if self.file_type == 'movie' or self.file_type == 'sequence':
            component = self.version_data.create_component(
                path=preview,
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
                path=thumb,
                data={'name': 'thumbnail'},
                location=server_location
            )

        elif self.file_type == 'image':
            component = self.version_data.create_component(
                path=self.path_object.preview_path,
                data={
                    'name': 'ftrackreview-image'
                },
                location=server_location
            )
            component['metadata']['ftr_meta'] = json.dumps({
                'format': 'image'
            })
            thumb_component = self.version_data.create_component(
                              path=self.path_object.thumb_path,
                              data={'name': 'thumbnail'},
                              location=server_location
            )

        self.version_data['thumbnail'] = thumb_component
        # we may need a qualifier for this to make sure it works.
        self.task_data['status'] = self.task_status_dict['Pending Review']
        logging.info('Committing Media')
        component.session.commit()
        thumb_component.session.commit()
        self.add_to_dailies()

    def create_review_session(self):
        self.ftrack.create('ReviewSession', {
            'name': 'Dailies %s' % datetime.date.today(),
            'description': "Review Session For Today's Data",
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
        if self.user_email:
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
                                       'parent.id is "{1}"'.format(self.task, self.entity_data['id']))
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

    def find_user(self, user=None):
        if not user:
            user = self.user_email
        if not self.user_data:
            self.user_data = self.ftrack.query('User where username is "{}"'.format(user)).first()
        self.add_user_to_project()
        return self.user_data

    def find_task(self):
        self.task_data = self.ftrack.query('Task where name is "{0}" '
                                           'and project.id is "{1}"'.format(self.task_name, self.project_data['id']))
        return self.task_data

    def find_version(self):
        self.version_data = self.ftrack.query('AssetVersion where asset_id is %s' % self.task_asset['id']).first()
        return self.version_data

    def get_status(self):
        self.project_data = self.entity_exists('project')
        self.find_task()
        if self.task_data:
            data = self.task_data.first()
            return data['status']['name']
            #return self.task_data['status']['name']
        else:
            print 'No Task Data found!'
            return None

    def get_url(self):
        print self.path_root
        if self.task:
            print 'task'
            return self.get_task_url(self.project, self.seq, self.shot, self.task, view='shot')
        if self.shot:
            print 'shot'
            return self.get_shot_url(self.project, self.seq, self.shot)
        elif self.asset:
            print 'asset not defined yet'
        if self.project:
            print 'project'
            return self.get_proj_url(self.project)

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
        task_string = None
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
            server_url = app_config()['project_management']['ftrack']['api']['server_url']
            api_key = app_config()['project_management']['ftrack']['api']['api_key']
            api_user = app_config()['project_management']['ftrack']['api']['api_user']
            schema = app_config()['project_management']['ftrack']['api']['default_schema']
            long_to_short = app_config()['project_management']['ftrack']['tasks'][schema]['long_to_short']
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


