import logging
try:
    from Queue import Empty
except ModuleNotFoundError:
    print('Python3 - Skipping Queue import')
from plugins.project_management.shotgun import shotgun_api3 as sg_api
from cgl.core.config import app_config

# TODO: This is a temporary fix until i can sort out the maya multi-threading issues
# TODO: This disables multi-threading for the Shotgun Queries

class ShotgunQueueEnd(object):
    pass


class ShotgunQuery(object):
    def __init__(self, type_, *args, **kwargs):
        self.result = None
        self.condition = None
        self.type = type_
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return """== Shotgun Query ==
%s
%s
%s
==================""" % (self.type, self.args, self.kwargs)

    @staticmethod
    def base_shotgun_query(type_, *args, **kwargs):
        config = app_config()['project_management']['shotgun']['api']
        connection = sg_api.Shotgun(base_url=str(config['server_url']),
                                    script_name=str(config['api_script']),
                                    api_key=str(config['api_key']))
        return getattr(connection, type_)(*args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return cls.base_shotgun_query("find", *args, **kwargs)

    @classmethod
    def find_one(cls, *args, **kwargs):
        return cls.base_shotgun_query("find_one", *args, **kwargs)

    @classmethod
    def schema_entity_read(cls, *args, **kwargs):
        return cls.base_shotgun_query("schema_entity_read", *args, **kwargs)

    @classmethod
    def schema_field_read(cls, *args, **kwargs):
        return cls.base_shotgun_query("schema_field_read", *args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.base_shotgun_query("create", *args, **kwargs)

    @classmethod
    def upload_thumbnail(cls, *args, **kwargs):
        return cls.base_shotgun_query("upload_thumbnail", *args, **kwargs)

    @classmethod
    def upload(cls, *args, **kwargs):
        return cls.base_shotgun_query("upload", *args, **kwargs)

    @classmethod
    def update(cls, *args, **kwargs):
        return cls.base_shotgun_query("update", *args, **kwargs)

    @classmethod
    def note_thread_read(cls, *args, **kwargs):
        return cls.base_shotgun_query("note_thread_read", *args, **kwargs)


class ShotgunProcess(object):
    STATES = {
        0: "init",
        1: "not connected",
        2: "connected",
        3: "query",
    }

    def __init__(self, id_, queue):
        ShotgunProcess.__init__(self, id_=id_, queue=queue)
        self.id_ = id_
        self.state = 0
        self.queue = queue
        self.connection = None

    def __str__(self):
        return "Shotgun processor(%s:%s) " % (self.id_, id(self.queue))

    def run(self):
        logging.debug("%s run" % self.__str__())
        task = self.queue.get(True)
        if not self.connection:
            import plugins.project_management.shotgun.shotgun_api3 as sg_api
            config = app_config()['project_management']['shotgun']['api']
            self.connection = sg_api.Shotgun(base_url=config['server_url'],
                                             script_name=config['api_script'],
                                             api_key=config['api_key'])

        result = getattr(self.connection, task.type)(*task.args, **task.kwargs)

        task.result['result'] = result
