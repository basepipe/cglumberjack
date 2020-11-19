from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import pymel.core as pm
from cgl.plugins.maya.utils import load_plugin


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        pass

