from cgl.plugins.blender import lumbermill as lm

import bpy
from cgl.core.utils.read_write import load_json
from cgl.plugins.blender.tasks.smart_task import SmartTask
from cgl.plugins.blender.lumbermill import LumberObject, scene_object, import_task, reference_file
from cgl.plugins.blender.utils import create_object, parent_object, read_matrix
# from cgl.plugins.blender.utils import get_next_namespace, select_reference
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.blender.utils import load_plugin
from cgl.core.config import app_config


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.lumbermill import scene_object
            self.path_object = scene_object()

    def _import(self, filepath, layout_group=None):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        bundle_import(filepath, layout_group)

    def import_latest(self, asset, task='bndl', category='*', type='env'):
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

        bndl_obj = scene_object().copy(task='bndl', seq=category, scope='assets', type=type, root=scene_object().root,
                                       shot=asset, context='render',
                                       user='publish', latest=True, filename='*', ext=None)

        for each in glob.glob(bndl_obj.path_root):
            print(each)
            if '.msd' in each:
                bundle_path = each

        if bundle_path:
            bundle_import(filepath=bundle_path)
        else:
            print('Could not glob bundle path at {}'.format(bndl_obj.path))

    def build(self):
        model_ref = import_task(task='mdl', reference=True)


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


def bundle_import(filepath, layout_group=None):
    """
    Accepts a 'bndl.json' file, processes it and imports all parts and reassembles it into the maya scene.
    :param filepath: path to the bndl.json
    :param layout_group: layout group to which to parent the bundle.
    :return:
    """
    relative_path = None
    root = app_config()['paths']['root']
    d = LumberObject(filepath)
    ns = d.shot
    #    try:
    #        pm.namespace(addNamespace=ns)
    #    except RuntimeError:
    #        # TODO - this needs to remove namespaces that are not wanted.
    #        print('Namespace %s exists, skipping creation' % ns)

    group = create_object('{}:bndl'.format(d.asset),collection = 'Collection')

    if 'COMPANIES/' in filepath:
        source_path = filepath.split("COMPANIES/")[1]
    else:
        source_path = filepath
    group['source_path'] = source_path

    group['useOutlinerColor']= True
    group['outlinerColor']= '1, 1, 0'
    layout_data = load_json(filepath)
    print('LAYOUT DATA____________')
    print(layout_data.keys())

    for each in layout_data:
        if layout_data[each]['source_path']:
            if 'source_path' in layout_data[each]:
                # this is a bundle, rather than a layout - unsure why this has changed so drastically
                # TODO - look at what's going on here.
                relative_path = layout_data[each]['source_path']
                transforms = layout_data[each]['transform'].split(' ')
            company = scene_object().company


        if root not in relative_path:

            reference_path = "%s\%s" % (root, relative_path)
        else:
            reference_path= relative_path
        float_transforms = [float(x) for x in transforms]

        d2 = LumberObject(reference_path)
        ns2 = get_next_namespace(d2.shot)
        print('namespace______')
        print(ns2)
        ref = reference_file(namespace=ns2,filepath=reference_path)
        read_matrix(ref,float_transforms)
        parent_object(ref,group)




    if layout_group:
        parent_object(group,layout_group)


def get_next_namespace(ns):
    import re
    pattern = '[0-9]+'
    next = False
    sel = bpy.data.objects
    latest = 0

    for i in sel:

        if ns in i.name:
            num = re.findall(pattern, i.name)
            if num:
                if int(num[-1]) > latest:
                    latest = int(num[-1])
            next = True

    if next:
        name = '{}{}'.format(ns, latest + 1)
        return name
    else:
        return ns
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


