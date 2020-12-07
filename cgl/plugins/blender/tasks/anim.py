from .smart_task import SmartTask
from cgl.plugins.blender import lumbermill as lm

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Read layout for file
        2. Import Camera
        :return:
        """
        lm.import_task(task='cam')
        lm.import_task(task='lay')

    def _import(self, filepath):
        pass

