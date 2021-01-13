import os
import pymel.core as pm
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.core.path import PathObject
from cgl.plugins.maya.alchemy import scene_object
from cgl.plugins.maya.utils import select_reference
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


def organize_assets():
    """
    puts references that aren't animated, and aren't bundles into a "LAYOUT" group
    :return:
    """
    anim_children = pm.listRelatives('ANIM', children=True)
    refs = pm.listReferences(refNodes=True)
    layout_refs = []
    bundle_children = task_bndl.get_bundle_children()

    for r in refs:
        node = select_reference(r[-1])
        if node not in anim_children and node not in bundle_children:
            layout_refs.append(node)

    pm.select(d=True)
    if layout_refs:
        if not pm.objExists('LAYOUT'):
            pm.group(name='LAYOUT')
        for lr in layout_refs:
            pm.parent(lr, 'LAYOUT')
        print('Layout Assets Organized')
    else:
        print('No Layout Assets to Organize')


def find_static_rigs():
    anim_children = pm.listRelatives('ANIM', children=True)
    bundle_children = task_bndl.get_bundle_children()
    refs = pm.listReferences(refNodes=True)
    static_rigs = []

    for r in refs:
        node = select_reference(r[-1])
        if node not in anim_children and node not in bundle_children and str(node).endswith('rig'):
            static_rigs.append(node)

    if static_rigs:
        print(static_rigs)
        if not pm.objExists('static_rigs'):
            pm.group(name='static_rigs')
            for s in static_rigs:
                pm.parent(s, 'static_rigs')
            print('Static Rigs have been Grouped')
            return static_rigs
    else:
        print('No Static Rigs')
        return False







