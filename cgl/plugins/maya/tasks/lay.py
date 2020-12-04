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


def general_import(ext):
    if ext == '.mb':
        print('.mb')
    elif ext == '.ma':
        print('.ma')
    elif ext == '.fbx':
        print('.fbx')
    elif ext == '.abc':
        print('.abc')
    elif ext == '.json':
        print('.json')
    elif ext == '.obj':
        print('.obj')


def add_bundles_to_layout(layout_json=None, next_version=False):
    if not layout_json:
        lay_obj = scene_object().copy(task='lay', latest=True, set_proper_filename=True, ext='json', user='publish',
                                      context='render')
        layout_json = lay_obj.path_root
    if os.path.exists(layout_json):
        asset_meta = assetcore.MetaObject(jsonfile=layout_json)
    else:
        asset_meta = assetcore.MetaObject()
    # find all bundles in scene
    bundles = task_bndl.get_bundles()
    for bndl in bundles:
        top_node = bndl.name()
        matrix = util.get_matrix(top_node)
        matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
        namespace = bndl.namespace()[:-1]
        bundle_json = pm.getAttr('%s.BundlePath' % bndl.name())
        asset_meta.add(_type='link',
                       name=namespace,
                       task='bndl',
                       type='link',
                       uid=namespace,
                       added_from=PathParser.relative_path(pm.sceneName()),
                       json=PathParser.relative_path(bundle_json),
                       transform=matrix)
    print('Adding Bundles to layout: %s' % layout_json)
    asset_meta.save(layout_json)
    return True


def add_link_to_layout(top_node, task, asset_json, layout_json=False, next_version=False, get_matrix=True):
    """
    adds a link to an existing layout.
    :param top_node:
    :param task:
    :param asset_json:
    :param layout_json:
    :param next_version:
    :param get_matrix:
    :return:
    """
    asset_json_object = LumberObject(asset_json)
    if pm.objExists(top_node):
        top_node = pm.PyNode(top_node)
        namespace = top_node.namespace()[:-1]
        if not namespace:
            namespace = top_node.name()
    else:
        print('node: %s does not exist' % top_node)
        return
    if not layout_json:
        layout_obj = scene_object().copy(task='lay', user='publish', latest=True, set_proper_filename=True, ext='json')
        layout_json = layout_obj.path_root
        layout_dir = os.path.dirname(layout_json)
        if not os.path.exists(layout_dir):
            from cgl.core.path import CreateProductionData
            CreateProductionData(layout_dir)
    if os.path.exists(layout_json):
        print('found existing layout.json {}'.format(layout_json))
        asset_meta = assetcore.MetaObject(jsonfile=layout_json)
    else:
        print('creating new layout.json {}'.format(layout_json))
        asset_meta = assetcore.MetaObject()
    if get_matrix:
        matrix = util.get_matrix(top_node.name())
        matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
    else:
        matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    asset_meta.add(_type='link',
                   name=namespace,
                   task=task,
                   type='link',
                   uid=namespace,
                   added_from=scene_object().path,
                   json=asset_json_object.path,
                   transform=None,
                   scope=asset_json_object.scope
                   )
    print('Adding %s to layout: %s' % (top_node, layout_json))
    asset_meta.save(layout_json)




