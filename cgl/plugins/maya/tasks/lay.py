import os
import pymel.core as pm
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.maya.lumbermill import LumberObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.core.assetcore as assetcore
import bndl as task_bndl

TASKNAME = os.path.basename(__file__).split('.py')[0]


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            self.path_object = scene_object()

    def _import(self, filepath):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        main_import(filepath)

    def import_latest(self, seq, shot):
        """
        imports the latest layout for a shot.
        :param seq:
        :param shot: Asset Cateogry
        :param task: Asset
        :return:
        """
        task = lay
        layout_obj = scene_object().copy(task='lay', seq=seq, shot=shot, context='render',
                                         user='publish', latest=True, filename='*', ext=None)
        for each in glob.glob(layout_obj.path_root):
            if '.json' in each:
                layout_path = each
        if layout_path:
            self._import(filepath=layout_path)
        else:
            print('Could not glob layout path at {}'.format(layout_obj.path))


def get_latest(ext='json'):
    this_obj = scene_object().copy(task=TASKNAME, context='render',
                                   user='publish', latest=True, set_proper_filename=True, ext=ext)
    return this_obj


def main_import(filepath):
    """

    :param filepath:
    :return:
    """
    layout_dict = load_json(filepath)
    print(layout_dict)






