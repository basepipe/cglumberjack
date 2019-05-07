

class ProjectManagementData(object):
    create = False
    edit = False
    delete = False

    def __init__(self, path_object, **kwargs):
        self.data = path_object
        print 'Creating Entries for '

    def create_entities_from_path_object(self):
        self.create_single_entity('project', self.data.project)
        self.create_single_entity('task', self.data.task)
        self.create_single_entity('user', self.data.user)
        # self.create_single_entity('time_entry', self.data.time_entry)

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

