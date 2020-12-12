from cgl.plugins.nuke.smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog

import cgl.plugins.maya.alchemy as alc


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
        prin('building plate')

    def _import(self, filepath):
        prin('importing Plate')
        pass

