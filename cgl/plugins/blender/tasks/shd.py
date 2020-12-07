from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.blender.utils import load_plugin
from cgl.plugins.blender import lumbermill as lm
import bpy


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        model_ref = lm.import_task(task='mdl', reference=True)
        lm.import_task(task='tex', ref_node=model_ref)

