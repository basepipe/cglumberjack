

class ProjectManagementData(object):
    create = False
    edit = False
    delete = False
    project = None
    task = None
    seq = None
    shot = None
    category = None
    asset = None
    user = None
    time_entry = None
    note = None

    def __init__(self, path_object=None, **kwargs):
        if path_object:
            for key in path_object.__dict__:
                self.__dict__[key] = path_object.__dict__[key]
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

        print 'Creating Entries for ftrack:'

    def create_entities_from_data(self):
        self.create_single_entity('project', self.project)
        self.create_single_entity('sequence', self.seq)
        self.create_single_entity('shot', self.shot)
        self.create_single_entity('category', self.category)
        self.create_single_entity('asset', self.asset)
        self.create_single_entity('task', self.task)
        self.create_single_entity('user', self.user)
        self.create_single_entity('time_entry', self.time_entry)
        self.create_single_entity('note', self.note)

    def create_single_entity(self, entity_type, entity_name):
        if entity_name:
            if not self.entity_exists(entity_type, entity_name):
                print 'Creating %s: %s' % (entity_type, entity_name)


    @staticmethod
    def entity_exists(data_type, name):
        """
        See if the entity exists within the project management system. This function is meant to be a wrapper to any
        API we encounter and is meant to keep core code as simple as possible throughout.
        :param data_type:
        :param name:
        :return: True if entity exists, false if it doesn't.
        """
        return False