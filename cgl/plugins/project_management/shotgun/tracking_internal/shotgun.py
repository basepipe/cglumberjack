import atexit
import logging
from Queue import Empty
from multiprocessing import Process, Queue, Manager

from cgl.core.config import app_config


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
        return """== Shotun Query ==
%s
%s
%s
==================""" % (self.type, self.args, self.kwargs)

    @staticmethod
    def base_shotgun_query(type_, *args, **kwargs):
        q = ShotgunQuery(type_,
                         *args,
                         **kwargs
                         )
        return ShotgunQueue().put_and_wait(q)

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


class ShotgunProcess(Process):
    STATES = {
        0: "init",
        1: "not connected",
        2: "connected",
        3: "query",
    }

    def __init__(self, id_, queue):
        Process.__init__(self)
        self.id_ = id_
        self.state = 0
        self.queue = queue
        self.connection = None
        logging.debug("%s Created" % self.__str__())

    def __str__(self):
        return "Shotgun proccessor(%s:%s:%s) " % (self.id_, id(self.queue), ShotgunProcess.STATES[self.state])

    def run(self):
        self.state = 1
        logging.debug("%s run" % self.__str__())
        while 1:
            try:
                task = self.queue.get(True)
                if isinstance(task, ShotgunQueueEnd):
                    break
                if not self.connection:
                    from plugins.project_management.shotgun import shotgun_api3 as sg_api
                    config = app_config()['shotgun']
                    self.connection = sg_api.Shotgun(base_url=config['url'],
                                                     script_name=config['api_script'],
                                                     api_key=config['api_key'])
                self.state = 3
                logging.debug("Shotgun.query  %s" % task.type)
                logging.debug("Shotgun.args   %s" % str(task.args))
                logging.debug("Shotgun.kwargs %s" % str(task.kwargs))

                result = getattr(self.connection, task.type)(*task.args, **task.kwargs)

                task.condition.acquire()
                task.result['result'] = result
                task.condition.notify()
                task.condition.release()
                self.state = 2
            except Empty:
                print "empty"
                pass



class ShotgunQueue(object):
    PROCESSES = []
    LOW_PROCCESSES = []
    QUEUE = Queue()
    LOW_QUEUE = Queue()
    MANAGER = None

    def __init__(self):
        if not ShotgunQueue.PROCESSES:
            ShotgunQueue.MANAGER = Manager()
            for proccess_number in range(0, app_config()['shotgun']['concurrent']):
                ShotgunQueue.PROCESSES.append(ShotgunProcess(proccess_number, ShotgunQueue.QUEUE))
            for low_proccess_number in range(0, app_config()['shotgun']['concurrent_low']):
                ShotgunQueue.LOW_PROCCESSES.append(ShotgunProcess(low_proccess_number, ShotgunQueue.LOW_QUEUE))

            for process in ShotgunQueue.PROCESSES:
                process.start()

            atexit.register(ShotgunQueue.__cleanup)

    @classmethod
    def put_and_wait(cls, query):
        query.condition = cls.MANAGER.Condition()
        query.result = cls.MANAGER.dict()
        query.condition.acquire()
        cls.QUEUE.put(query)
        query.condition.wait()
        query.condition.release()
        return query.result['result']

    @staticmethod
    def __cleanup():
        for _ in ShotgunQueue.PROCESSES:
            ShotgunQueue.QUEUE.put(ShotgunQueueEnd())
        for _ in ShotgunQueue.LOW_PROCCESSES:
            ShotgunQueue.LOW_QUEUE.put(ShotgunQueueEnd())
