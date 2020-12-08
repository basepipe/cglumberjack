from .smart_task import SmartTask
import cgl.plugins.maya.lumbermill as lm


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        lm.import_task(task='cam')
        lm.import_task(task='anim')
        lm.import_and_attach_shaders()

    def _import(self, filepath):
        pass
