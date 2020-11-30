from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.houdini import lumbermill as lm
import cProfile

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.houdini.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        ref_path = lm.import_task(task='mdl', reference=True)
        cProfile.runctx("lm.import_task(task='tex')",globals(),locals())

