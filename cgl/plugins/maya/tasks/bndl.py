import os
import pymel.core as pm
from cgl.core.utils.read_write import load_json, save_json
from .smart_task import SmartTask
from cgl.core.path import PathObject
from cgl.plugins.maya.alchemy import scene_object
import cgl.plugins.maya.utils as utils
from cgl.ui.widgets.dialog import InputDialog
from cgl.core.config.config import get_root
import cgl.plugins.maya.tasks.mdl as mdl
reload(mdl)

TASKNAME = os.path.basename(__file__).split('.py')[0]


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            self.path_object = scene_object()
        print('Bndl, {}'.format(self.path_object.project_msd_path))

    def _import(self, filepath, layout_group=None):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        bundle_import(filepath, layout_group)

    def import_published_msd(self):
        """
        imports the latest publish file for the given seq/shot combination
        :param task:
        :param category: Asset Cateogry
        :param asset: Asset
        :return:
        """
        msd_dict = load_json(self.path_object.project_msd_path)
        msd = msd_dict['assets'][self.path_object.seq][self.path_object.shot][self.path_object.task]
        bundle_import(msd)

    def export_msd(self, selected=None):
        """
        exports the selected bndle as an msd file.
        format example for bndl:
        {
            "presentPile1": {
                "category": "Prop",
                "msd_path": "VFX/render/02BTH_2021_Kish/assets/Prop/presentPile/mdl/publish/004.000/high/Prop_presentPile_mdl.msd",
                "name": "presentPile",
                "task": "mdl",
                "transform": {
                    "matrix": "-1.64649598661 -0.0125312913377 -2.15273456447 0.0 0.00236906607631 2.71017660235 -0.0175881741261 0.0 2.15276973359 -0.012566745027 -1.646449733 0.0 18.9753119694 2.28237451241 5.23043842313 1.0"
                    "scale": {}
                    "rotate": {}
                    "translate": {}
                }
        }
        :return:
        """
        if not selected:
            print(self.path_object.msd_path)
            save_json(self.path_object.msd_path, get_msd_info(TASKNAME))


def get_msd_info(bndl):
    """
    returns the msd dict for the given task.
    :return:
    """

    bndl_dict = {}
    meshes = {}
    children = pm.listRelatives(bndl, children=True)
    if children:
        for child in children:
            clean_name = child.namespace().replace(':', '')
            meshes[clean_name] = mdl.get_msd_info(child)
    bndl_dict['attrs'] = {'meshes': meshes}
    bndl_dict['source_file'] = scene_object().path
    return bndl_dict


def get_latest_publish(filepath, task='bndl', ext='.json'):
    """
    gets the latest published version of the path_object.
    :return:
    """
    bundle_path = None
    bndl_obj = PathObject(filepath).copy(task=task, context='render',
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


def get_bundle_children():
    bundles = get_bundles()
    bundle_children = []
    for b in bundles:
        for child in pm.listRelatives(b, children=True):
            bundle_children.append(child)
    return bundle_children


def bundle_import(filepath, layout_group=None):
    """
    Accepts a 'bndl.json' or bndl.msd file, processes it and imports all parts and reassembles it into the maya scene.
    :param filepath: path to the bndl.json
    :param layout_group: layout group to which to parent the bundle.
    :return:
    """
    relative_path = None
    d = PathObject(filepath)
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
        reference_path = "%s/%s%s" % (get_root(d.project), d.company, relative_path)
        float_transforms = [float(x) for x in transforms]
        d2 = PathObject(reference_path)
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

