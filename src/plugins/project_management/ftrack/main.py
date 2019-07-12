import logging
import json
from cglcore.config import app_config
import ftrack_api


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
    ftrack_asset_type = 'Upload'
    type = None
    thumb_path_full = None

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]
        self.shot_name = '%s_%s' % (self.seq, self.shot)
        if not self.user_email:
            self.user_email = app_config()['project_management']['ftrack']['api']['api_user']
            if not self.user_email:
                print 'No User Email Defined, cant create Ftrack Production Data'
                return

        if not self.project:
            print 'No Project Defined'
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

        self.ftrack = ftrack_api.Session(server_url=app_config()['project_management']['ftrack']['api']['server_url'],
                                         api_key=app_config()['project_management']['ftrack']['api']['api_key'],
                                         api_user=app_config()['project_management']['ftrack']['api']['api_user'])

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
        ftrack_tasks = schema['long_to_short'][self.scope.lower()]
        for t in ftrack_tasks:
            if ftrack_tasks[t] == self.task:
                full_name = t

        for task in self.task_types:
            print '\t', task['name'], full_name
            if task['name'] == full_name:
                return task
        print 'Could Not Find a Task of %s' % task['name']
        return None

    def create_project_management_data(self):
        self.project_data = self.entity_exists('project')
        if not self.project_data:
            if self.project:
                self.project_data = self.create_project()
            else:
                print 'No Project Defined, Skipping Project creation'
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
            data_ = self.find_asset()
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
            data_ = self.find_version()
        try:
            if data_:
                logging.info('Found %s: %s, No Need to Create' % (data_type, data_['name']))
            return data_
        except:
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
        logging.info('Creating Asset %s' % self.asset)
        self.asset_data = self.ftrack.create('AssetBuild', {
            'name': self.asset,
            'parent': self.project_data
        })
        return self.asset_data

    def create_sequence(self):
        logging.info('Creating Sequence %s' % self.seq)
        self.seq_data = self.ftrack.create('Sequence', {
            'name': self.seq,
            'parent': self.project_data
        })
        return self.seq_data

    def create_shot(self):
        self.shot_name = '%s_%s' % (self.seq, self.shot)
        logging.info("Creating Shot %s" % self.shot_name)
        self.shot_data = self.ftrack.create('Shot', {
            'name': self.shot_name,
            'parent': self.seq_data,
            'status': self.default_shot_status
        })
        return self.shot_data

    def create_task(self):
        logging.info('Creating Task %s, %s' % (self.task_name, self.task_type['name']))
        self.task_data = self.ftrack.create('Task', {
            'name': self.task_name,
            'parent': self.entity_data,
            'status': self.default_task_status,
            'type': self.task_type
        })
        if self.thumb_path_full:
            print self.thumb_path_full
            # self.task_data.create_thumbnail(self.thumb_path_full)
        return self.task_data

    def create_assignment(self):
        print 'Checking for Assignment %s' % self.task_data['name']
        existing_assignment = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="assignment"'.format(
                self.task_data['id'], self.user_data['id'])).first()
        if not existing_assignment:
            print 'Creating Assignment %s: for %s' % (self.task, self.user_email)
            self.assignment_data = self.ftrack.create('Appointment', {
                'context': self.task_data,
                'resource': self.user_data,
                'type': 'assignment'
            })
            return self.assignment_data
        else:
            print 'Found Assignment: %s -->> %s' % (self.user_email, self.task_name)
            return None

    def create_version(self):
        try:
            self.ftrack.event_hub.connect()
        except:
            pass
        # TODO - need to look at if an "asset" exists already before creating it.
        # TODO - need to look at whether a "version" exists already before creating it.
        asset_type = self.ftrack.query('AssetType where name is "%s"' % self.ftrack_asset_type).one()
        asset = self.ftrack.create('Asset', {
            'name': self.version,
            'type': asset_type,
            'parent': self.entity_data
        })
        if not asset:
            print 'Type: %s not found in ftrack - aborting' % self.task
            return
        print 'Creating Version %s for: %s' % (self.version, self.task_name)
        self.version_data = self.ftrack.create('AssetVersion', {
            'asset': asset,
            'task': self.task_data,
        })
        #if self.thumb_path_full:
        #    self.version_data.create_thumbnail(self.thumb_path_full)

    def upload_media2(self):
        print 'Encoding Media For: %s' % 'This thing'
        self.ftrack.encode_media(self.path_root)

    def upload_media(self):
        # TODO - need methods for deriving filetype as well as frameIn, frameOut, and frameRate
        server_location = self.ftrack.query('Location where name is "ftrack.server"').one()
        component = self.version_data.create_component(
            path=self.path_root,
            data={
                'name': self.version
            },
            location=server_location
        )
        if self.file_type == 'movie':
            component['metadata']['ftr_meta'] = json.dumps({
                'frameIn': 0,
                'frameOut': 150,
                'frameRate': 24
            })
        elif self.file_type == 'image':
            component['metadata']['ftr_meta'] = json.dumps({
                'format': 'image'
            })
        print 'Committing Media'
        component.session.commit()
        print 'Encoding Media'
        self.ftrack.encode_media(component)

    def add_group_to_project(self):
        self.user_group = self.ftrack.query('Group where name is %s' % self.user_group_name)[0]
        self.user_data = self.ftrack.query('User where username is "{}"'.format(self.user_email)).one()
        new_membership = self.ftrack.ensure('Membership', {"group_id": self.user_group['id'],
                                                           "user_id": self.user_data['id']})
        project_has_group = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="allocation"'.format(
                self.project_data['id'], self.user_group['id']
            )
        ).first()

        if not project_has_group:
            logging.info('Assigning group {} to project {}'.format(self.user_group ['name'],
                                                                   self.project_data['name']))
            self.ftrack.create('Appointment', {
                'context': self.project_data,
                'resource': self.user_group,
                'type': 'allocation'
            })
        else:
            logging.info('Group {} already in assigned to project {}'.format(self.user_group ['name'],
                                                                             self.project_data['name']))

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
            logging.info('Assigning user {} to project {}'.format(self.user_data['username'], self.project_data['name']))
            self.ftrack.create('Appointment', {
                'context': self.project_data,
                'resource': self.user_data,
                'type': 'allocation'
            })

        else:
            logging.info('User {} already in assigned to project {}'.format(self.user_data['username'], self.project_data['name']))

    def find_project(self):
        try:
            self.project_data = self.ftrack.query('Project where status is active and name is %s' % self.project_short_name).first()
            if self.project_data:
                return self.project_data
            else:
                logging.info('%s Not Found' % self.project)
                return False
        except AttributeError:
            logging.info('No Ftrack Project Found, skipping')
            pass

    def find_asset(self):
        asset = self.ftrack.query('AssetBuild where '
                                  'name is "%s" and project.id is "%s"' % (self.asset, self.project_data['id'])).first()
        if asset:
            self.asset_data = asset
            return self.asset_data
        else:
            return self.create_asset()

    def find_shot(self):
        self.shot_data = self.ftrack.query('Shot where name is %s' % self.shot_name).first()
        return self.shot_data

    def find_seq(self):
        seqs = self.ftrack.query('Sequence where project.id is "{0}"'.format(self.project_data['id']))
        for each in seqs:
            if each['name'] == self.seq:
                logging.info('Found %s' % each['name'])
                self.seq_data = each
                return each
        return None

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
            self.user_data = self.ftrack.query('User where username is "{}"'.format(self.user_email)).one()
        self.add_user_to_project()
        return self.user_data

    def find_task(self):
        self.task_data = self.ftrack.query('Task where name is "{0}" '
                                           'and project.id is "{1}"'.format(self.task_name, self.project_data['id']))
        return self.task_data

    def find_version(self):
        return self.ftrack.query('AssetVersion where '
                                 'task.id is "{0}"'.format(self.task_data['id']))
        pass


if __name__ == "__main__":
    this = ProjectManagementData()
    this.create_project_management_data()
    this.ftrack.commit()
    #this.upload_media()



