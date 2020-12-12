import pymel.core as pm
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.maya.lumbermill import LumberObject, scene_object
import cgl.plugins.maya.utils as utils
reload(utils)
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.maya.utils import load_plugin
from cgl.core.config import app_config


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            self.path_object = scene_object()
        print('Bndl, {}'.format(self.path_object))

    def _import(self, filepath, layout_group=None):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        bundle_import(filepath, layout_group)

    def import_latest(self, asset, task='bndl', category='*'):
        """
        imports the latest publish file for the given seq/shot combination
        :param task:
        :param category: Asset Cateogry
        :param asset: Asset
        :return:
        """
        import os
        import glob
        bundle_path = None
        bndl_obj = scene_object().copy(task='bndl', seq=category, shot=asset, context='render',
                                       user='publish', latest=True, filename='*', ext=None)
        for each in glob.glob(bndl_obj.path_root):
            if '.json' in each:
                bundle_path = each
        if bundle_path:
            bundle_import(filepath=bundle_path)
        else:
            print('Could not glob bundle path at {}'.format(bundle_obj.path))


def get_latest_publish(filepath, task='bndl', ext='.json'):
    """
    gets the latest published version of the path_object.
    :return:
    """
    bundle_path = None
    bndl_obj = LumberObject(filepath).copy(task=task, context='render',
                                           user='publish', latest=True, filename='*', ext=None)
    for each in glob.glob(bndl_obj.path_root):
        if ext in each:
            bundle_path = each
    if bundle_path:
        return bundle_path
    else:
        print('Could not glob bundle path at {}'.format(bundle_obj.path))
        return None


def get_bundles():
    """
    get s alist of bundles in the scene.
    :return:
    """
    bundles = []
    sel = pm.ls(type='transform')
    for obj in sel:
        if obj.hasAttr('BundlePath'):
            bundles.append(obj)
    return bundles


def bundle_import(filepath, layout_group=None):
    """
    Accepts a 'bndl.json' file, processes it and imports all parts and reassembles it into the maya scene.
    :param filepath: path to the bndl.json
    :param layout_group: layout group to which to parent the bundle.
    :return:
    """
    relative_path = None
    d = LumberObject(filepath)
    og_ns = d.shot
    ns = utils.get_namespace(filepath)
    try:
        pm.namespace(addNamespace=ns)
    except RuntimeError:
        # TODO - this needs to remove namespaces that are not wanted.
        print('Namespace %s exists, skipping creation' % ns)
        return
    pm.namespace(set=ns)
    pm.select(d=True)
    group = pm.group(name='bndl')
    pm.namespace(set=':')
    pm.addAttr(group, ln='BundlePath', dt='string')
    pm.setAttr('%s.BundlePath' % group, filepath)
    pm.setAttr('%s.useOutlinerColor' % group, True)
    pm.setAttr('%s.outlinerColor' % group, (1, 1, 0))
    layout_data = load_json(filepath)
    print(layout_data)
    child_transforms = []
    for each in layout_data:
        if 'attributes' in layout_data[each].keys():
            relative_path = layout_data[each]['attributes']['maya_path']
            transforms = layout_data[each]['attributes']['transform'].split(' ')
            child_transforms = layout_data[each]['attributes']['children']
        elif 'source_path' in layout_data[each]:
            # this is a bundle, rather than a layout - unsure why this has changed so drastically
            # TODO - look at what's going on here.
            relative_path = layout_data[each]['source_path']
            transforms = layout_data[each]['transform'].split(' ')
        reference_path = "%s/%s%s" % (app_config()['paths']['root'], d.company, relative_path)
        float_transforms = [float(x) for x in transforms]
        d2 = LumberObject(reference_path)
        print(reference_path)
        print d2.path_root
        print d2.shot
        ns2 = utils.get_next_namespace(d2.shot)
        ref = pm.createReference(reference_path, namespace=ns2, ignoreVersion=True, loadReferenceDepth='all')
        namespace_ = pm.referenceQuery(ref, ns=True)  # ref.namespace
        object_ = '%s:mdl' % namespace_

        if 'rig' in relative_path:
            object_ = '%s:rig' % namespace_
        pm.xform(object_, m=float_transforms)
        if child_transforms:
            for child in child_transforms:
                original_ns = child.split(':')[0]
                ns_clean = namespace_.replace(':', '')
                child2 = child.replace(original_ns, ns_clean)
                ts = child_transforms[child].split(' ')
                fl_transforms = [float(x) for x in ts]
                pm.xform(child2, m=fl_transforms)
        ref_node = utils.select_reference(ref)
        pm.select(d=True)
        pm.parent(ref_node, group)
        pm.select(d=True)
        if layout_group:
            pm.parent(group, layout_group)
        pm.select(d=True)
    return group


def remove_selected_bundle():
    bndl = pm.ls(sl=True)[0]
    if bndl:
        if pm.attributeQuery('BundlePath', node=bndl, exists=True):
            # return the children of the bundle node
            for each in pm.listRelatives(bndl, children=True):
                ref = pm.referenceQuery(each, rfn=True)
                pm.FileReference(ref).remove()
            pm.delete(bndl)
        else:
            print('ERROR: no BundlePath attr found')
    else:
        print('ERROR: Nothing Selected')

