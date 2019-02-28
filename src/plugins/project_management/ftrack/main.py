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
    shot = '0400'
    shot_name = '%s_%s' % (seq, shot)
    shot_data = None
    category = None
    asset = None
    user = 'Lone Coconut'
    user_email = 'LoneCoconutMail@gmail.com'
    user_data = None
    time_entry = None
    note = None
    schema = SCHEMAS[3]
    schema_data = None
    version = 'compositing.nk'
    version_data = None
    entity_data = None
    asset_data = None
    scope = 'shots'
    task_name = None
    project_team = None
    assignments = []
    assignment_data = None
    user_group_name = 'default'
    user_group = None
    appointment = None

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
        self.task_type = self.get_current_task_type()
        self.task_statuses = self.project_schema.get_statuses('Task', self.task_type['id'])
        self.default_task_status = self.project_schema.get_statuses('Task', self.task_type['id'])[0]

        print 'Creating Entries for ftrack:'

    def get_current_task_type(self):
        for task in self.task_types:
            if task['name'] == self.task:
                return task
        return None

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
        if self.user_email:
            self.entity_exists('user')
            if self.user_data:
                # TODO - add user to the project if they aren't on it.
                self.create_assignment()

        if self.version:
            print 'Looking for Assets'
            create_version = True
            if self.scope == 'shots':
                assets = self.ftrack.query('Asset where parent.name is %s' % self.shot_name)
                if assets:
                    for a in assets:
                        print 'Found version: %' % a['name']
                        if a['name'] == self.version:
                            print '%s already exists, skipping' % self.version
                            create_version = False
                            return
                else:
                    if create_version:
                        self.create_version()

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
        elif data_type == 'version':
            data_ = self.find_version()
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

    #def create_asset(self):
    #    asset = self.ftrack.create('Asset', {
    #        'name': self.asset,
    #        'type': 'Character',
    #        'parent': self.project_data
    #    })
    #    return asset

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
        print 'Creating Task %s, %s' % (self.task_name, self.task_type['name'])
        self.task_data = self.ftrack.create('Task', {
            'name': self.task_name,
            'parent': self.shot_data,
            'status': self.default_task_status,
            'type': self.task_type
        })
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
        # TODO - need to look at if an "asset" exists already before creating it.
        # TODO - need to look at whether a "version" exists already before creating it.
        asset_type = self.ftrack.query('AssetType where name is "%s"' % self.task).one()
        asset = self.ftrack.create('Asset', {
            'name': self.version,
            'type': asset_type,
            'parent': self.shot_data
        })

        print 'Creating Version %s for: %s' % (self.version, self.task_name)
        if self.scope == 'shots':
            self.version_data = self.ftrack.create('AssetVersion', {
                'asset': asset,
                'task': self.task_data,
            })

    def add_user_group_to_project(self):
        self.user_group = self.ftrack.ensure('Group', {"name": self.user_group_name, "local": False})
        project_has_group = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="allocation"'.format(
                self.project_data['id'], self.user_group['id']
            )
        ).first()
        if not project_has_group:
            print 'Assigning group {} to project {}'.format(self.user_group['name'], self.project_data['name'])
            self.ftrack.create('Appointment', {
                'context': self.project_data,
                'resource': self.user_group,
                'type': 'allocation'
            })
        else:
            print 'Found Group: {} on project {}'.format(self.user_group['name'], self.project_data['name'])

    def add_user_to_project(self):
        self.find_project()
        self.find_user()
        print 'Assigning user {} to {} {}'.format(self.user_data['username'], 'project', self.project_data['name'])
        self.appointment = self.ftrack.create('Appointment', {
            'context': self.project_data,
            'resource': self.user_data,
            'type': 'allocation'
        })
        print 'made it to the end'

    def find_project(self):
        self.project_data = self.ftrack.query('Project where status is active and name is %s' % self.project_short_name).first()
        if self.project_data:
            print 'Found Project: %s' % self.project
            return self.project_data
        else:
            print '%s Not Found' % self.project
            return False

    def find_asset(self):
        return self.ftrack.query('Asset where status is active and '
                                 'project.id is "{0}"'.format(self.project_data['id']))

    def find_shot(self):
        self.shot_data = self.ftrack.query('Shot where name is %s' % self.shot_name).first()
        return self.shot_data

    def find_seq(self):
        self.seq_data = self.ftrack.query('Sequence where' 
                                          ' project.id is "{0}"'.format(self.project_data['id']))
        return self.seq_data

    def find_project_team(self):
        self.project_team = set()
        for allocation in self.project_data['allocations']:
            resource = allocation['resource']

            if isinstance(resource, self.ftrack.types['Group']):
                for membership in resource['memberships']:
                    user = membership['user']
                    self.project_team.add(user)

    def find_user(self):
        # this should be easier than this - but the example given in the docs isn't working
        # will have to reach out to support on this one
        # http://ftrack-python-api.rtd.ftrack.com/en/1.7.0/example/assignments_and_allocations.html
        # i should be able to do this easily with a query but it doesn't return anything.
        all_users = self.ftrack.query('User')
        for each in all_users:
            if each['username'] == self.user_email:
                self.user_data = each
                print 'Found User: %s' % self.user_email
                self.add_user_group_to_project()
                self.find_user_on_project(context='project')
        return self.user_data

    def find_user_on_project(self, context='project'):
        if context == 'project':
            context = self.project_data
        else:
            context == self.user_group

        project_has_user = self.ftrack.query(
            'Appointment where context.id is "{}" and resource.id = "{}" and type="allocation"'.format(
                self.project_data['id'], self.user_data['id']
            )
        ).first()
        if not project_has_user:
            self.add_user_to_project()
        else:
            print 'Found User: {} on project {}'.format(self.user_data['username'], self.project_data['name'])

    def find_user_tasks(self):
            self.find_project()
            self.assignments = self.ftrack.query('select link from Task '
                                                 'where assignments any (resource.username = %s)' % self.user_email)

            print 'assignments found for %s:' % self.user_email
            for a in self.assignments:
                print ' / '.join(item['name'] for item in a['link'])
            return self.assignments

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
    # this.find_user()
    this.create_project_management_data()
    this.ftrack.commit()


