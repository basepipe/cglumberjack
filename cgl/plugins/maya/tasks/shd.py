from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import pymel.core as pm
from cgl.plugins.maya.utils import load_plugin
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
        model_ref = lm.import_task(task='mdl', reference=True)
        lm.import_task(task='tex', ref_node=model_ref)

    def _import(self, filepath):
        pass

