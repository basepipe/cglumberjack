import os
import pymel.core as pm
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.maya.lumbermill import LumberObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.core.assetcore as assetcore
import bndl as task_bndl
reload(task_bndl)


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
    print 'Adding Bundles to layout: %s' % layout_json
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
        print 'node: %s does not exist' % top_node
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
    print 'Adding %s to layout: %s' % (top_node, layout_json)
    asset_meta.save(layout_json)


def export_layout(next_version=True):
    """
    exports a layout of the current scene
    :return:
    """
    lobj = scene_object().copy(task='lay', latest=True, set_proper_filename=True, ext='json', user='publish',
                               context='render')
    if next_version:
        lobj = lobj.next_major_version()
        os.makedirs(os.path.dirname(lobj.path_root))
    json_render_path = lobj.path_root

    if json_render_path:
        asset_meta = assetcore.MetaObject()
        excluded_bundle_refs = []
        # add bundles
        sel = pm.ls(type='transform')
        # TODO: I need a function to return bundles
        for obj in sel:
            if obj.hasAttr('BundlePath'):
                top_node = obj.name()
                matrix = get_matrix(top_node)
                matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
                namespace = obj.namespace()[:-1]
                json_path = pm.getAttr('%s.BundlePath' % obj.name())
                json_path_obj = LumberObject(json_path)

                asset_meta.add(_type='bundle',
                               bundlename=json_path_obj.shot,
                               uid=namespace,
                               source_path=scene_object().path,
                               bundle_path=json_path_obj.path,
                               transform=matrix)

                # exclude children references from the bundle
                children = pm.listRelatives(obj, ad=True)
                for child in children:
                    try:
                        ref = pm.referenceQuery(child, filename=True, wcn=True)
                        excluded_bundle_refs.append(ref)
                    except RuntimeError:
                        logging.info('%s is not a reference' % child)
        # add all references
        sel = pm.listReferences()
        assets = {}

        for obj in sel:
            if obj.isLoaded():
                top_node = obj.nodes()[0]
                temp_obj = LumberObject(obj.path)
                tag_volume_movable = False
                if top_node.hasAttr('static_volume_object'):
                    if pm.getAttr('%s.static_volume_object' % top_node):
                        tag_volume_movable = True

                matrix = get_matrix(top_node)
                matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
                namespace = top_node.namespace()[:-1]
                path = pm.referenceQuery(obj, filename=True, wcn=True)
                path_obj = LumberObject(path)
                if namespace:
                    if path not in excluded_bundle_refs:
                        asset_meta.add(_type='asset',
                                       uid=namespace,
                                       name=temp_obj.shot,
                                       assetname=temp_obj.shot,
                                       task=temp_obj.task,
                                       source_path=path_obj.path,
                                       transform=matrix)
        asset_meta.save(json_render_path)

        return json_render_path
    else:
        return False