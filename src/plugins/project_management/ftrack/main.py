from core.config import app_config
import ftrack_api

SCHEMAS = ['Generic', 'Development', 'INTERNO', "VFX", 'PRODUCCION', 'ANIMATION']  # These are queryable
ASSET_CATEGORIES = ['Character', 'Environment', 'Prop', 'Matte Painting']  # These are queryable


class ProjectManagementData(object):
    create = False
    edit = False
    delete = False
    project = 'cgl_test_full'
    project_short_name = 'cgl_test'
    project_data = None
    task = 'Compositing'
    task_data = None
    seq = 'CGLT'
    seq_data = None
    shot = '0000'
    shot_name = '%s_%s' % (seq, shot)
    shot_data = None
    category = None
    asset = None
    user = None
    time_entry = None
    note = None
    schema = SCHEMAS[3]
    schema_data = None
    version_data = None
    entity_data = None
    asset_data = None
    scope = 'shots'
    task_name = None

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

        self.ftrack = ftrack_api.Session(server_url=app_config()['ftrack']['server_url'],
                                         api_key=app_config()['ftrack']['api_key'],
                                         api_user=app_config()['ftrack']['api_user'])

        self.project_schema = self.ftrack.query('ProjectSchema where name is %s' % self.schema).first()
        # Retrieve default types.
        self.default_shot_status = self.project_schema.get_statuses('Shot')[0]
        self.shot_statuses = self.project_schema.get_statuses('Shot')
        self.task_types = self.project_schema.get_types('Task')
        self.default_task_type = self.project_schema.get_types('Task')[0]
        self.task_statuses = self.project_schema.get_statuses('Task', self.default_task_type['id'])
        self.default_task_status = self.project_schema.get_statuses('Task', self.default_task_type['id'])[0]

        print 'Creating Entries for ftrack:'

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
                    print '2 task data: %s' % self.task_data


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
            data_ = self.find_seq()[0]
        elif data_type == 'shot':
            data_ = self.find_shot()
        elif data_type == 'user':
            data_ = self.find_user()
        elif data_type == 'task':
            data_ = self.find_task()
            if data_:
                data_ = data_[0]
        try:
            if data_:
                print 'Found %s: %s' % (data_type, data_['name'])
            return data_
        except:
            return None

    def create_project(self):
        print 'Creating Project %s' % self.project
        project = self.ftrack.create('Project', {
            'name': self.project_short_name,
            'full_name': self.project,
            'project_schema': self.project_schema
        })
        return project

    def create_asset(self):
        asset = self.ftrack.create('Asset', {
            'name': self.asset,
            'type': 'Character',
            'parent': self.project_data
        })
        return asset

    def create_sequence(self):
        print 'Creating Sequence %s' % self.seq
        self.seq_data = self.ftrack.create('Sequence', {
            'name': self.seq,
            'parent': self.project_data
        })
        return self.seq_data

    def create_shot(self):
        print "Creating Shot %s" % self.shot_name
        self.shot_data = self.ftrack.create('Shot', {
            'name': self.shot_name,
            'parent': self.seq_data,
            'status': self.default_shot_status
        })
        return self.shot_data

    def create_task(self):
        print 'Creating Task %s' % self.task_name
        self.task_data = self.ftrack.create('Task', {
            'name': self.task,
            'parent': self.shot_data,
            'status': self.default_task_status,
            'type': self.default_task_type
        })
        return self.task_data

    def create_version(self):
        self.version_data = self.ftrack.create('Version', {
            'name': self.version,
            'parent': self.task_data,
        })
        return self.version_data

    def find_project(self):
        print 'Searching for Project %s' % self.project
        self.project_data = self.ftrack.query('Project where status is active and name is %s' % self.project_short_name).first()
        if self.project_data:
            print 'Project %s Found' % self.project
            return self.project_data
        else:
            print '%s Not Found' % self.project
            return False

    def find_asset(self):
        return self.ftrack.query('Asset where status is active and '
                                 'project.id is "{0}"'.format(self.project_data['id']))

    def find_shot(self):
        print 'Searching for shot %s' % self.shot_name
        self.shot_data = self.ftrack.query('Shot where name is %s' % self.shot_name).first()
        return self.shot_data

    def find_seq(self):
        self.seq_data = self.ftrack.query('Sequence where' 
                                          ' project.id is "{0}"'.format(self.project_data['id']))
        return self.seq_data
        pass

    def find_user(self):
        pass

    def find_task(self):
        return self.ftrack.query('Task where '
                                 'project.id is "{0}"'.format(self.project_data['id']))
        pass

    def find_version(self):
        pass

    def test(self):
        project_schema = self.ftrack.query('ProjectSchema')
        for each in project_schema:
            print each['name']
        return
        self.find_project()
        assets = self.find_asset()
        for a in assets:
            print a['name']


if __name__ == "__main__":
    this = ProjectManagementData()
    this.create_project_management_data()
    this.ftrack.commit()


