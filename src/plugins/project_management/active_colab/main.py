#from core.path import PathObject


class ProjectManagementData(object):
    create = False
    edit = False
    delete = False
    project = None
    task = None
    user = None
    time_entry = None

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

        print 'Creating Entries for Active Colab:'

    def create_entities_from_path_object(self):
        self.create_single_entity('project', self.project)
        self.create_single_entity('task', self.task)
        self.create_single_entity('user', self.user)

    def create_single_entity(self, entity_type, entity_name):
        if entity_name:
            if not self.entity_exists(entity_type, entity_name):
                print 'Creating %s: %s' % (entity_type, entity_name)

    def edit_entity(self, **kwargs):
        print 'Editing %s: %s' % (self.data_type, self.data.data[self.data_type])

    def delete_entity(self, **kwargs):
        print 'Deleting %s: %s' % (self.data_type, self.data.data[self.data_type])

    def entity_exists(self, data_type, name):
        return False

