import os
import glob
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.blender.alchemy import PathObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.core.assetcore as assetcore
import bpy
from .mdl import get_msd_info
from . import mdl
from . import rig
from . import cam


TASKNAME = os.path.basename(__file__).split('.py')[0]


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            self.path_object = scene_object()

    def _import(self, filepath, import_rigs = True,reference = True ,task=None,latest =False, **kwargs):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        from cgl.plugins.blender.alchemy import  set_relative_paths
        main_import(filepath,import_rigs,reference,latest)
        set_relative_paths(True)

    def build(self):
        from cgl.plugins.blender.utils import create_shot_mask_info,set_collection_name, create_object
        from cgl.plugins.blender import alchemy as alc
        create_shot_mask_info()
        set_collection_name()
        bndl_group = create_object('lay')
        default_list = ['FG','BG','MAIN','CAMERAS']
        for layer in default_list :
            create_object(layer, parent=bndl_group)
            create_object('BG', parent=bndl_group)
            create_object('MAIN', parent=bndl_group)

        alc.import_task(task='cam')


    def import_latest(self, seq=None, shot= None, import_rigs = True,reference=True,latest = False,**kwargs):
        """
        imports the latest layout for a shot.
        :param seq:
        :param shot: Asset Cateogry
        :param task: Asset
        :return:
        """
        layout_path = None
        if seq == None:
            self.seq = scene_object().seq
        if shot == None:
            self.shot = scene_object().shot

        layout_obj = scene_object().copy(task='lay', seq=self.seq, shot=self.shot, context='render',
                                         user='publish', latest=True, filename='*', ext=None)

        for each in glob.glob(layout_obj.path_root):
            if '.msd' in each:
                layout_path = each
        if layout_path:
            self._import(filepath=layout_path, import_rigs= import_rigs,reference=reference, latest = latest)
        else:
            print('Could not glob layout path at {}'.format(layout_obj.path))

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
        main_import(msd)

    def export_msd(self, selected=None):
        """

        """
        if not selected:
            print(self.path_object.msd_path)
            save_json(self.path_object.msd_path, get_msd_info(TASKNAME))

    def get_msd_info(self, bndl= None ):
        """
        returns the msd dict for the given task.
        :return:
        """
        from ..utils import get_object
        bndl_dict = {}
        meshes_dict = {}
        meshes = {}
        rigs = {}
        bundles = {}
        cameras = {}
        children = get_object('lay').children

        objects=  []
        bundles_items = []
        rig_items = []

        if children:
            for child in children:
                for obj in child.children:
                    objects.append(obj)

        for mesh in objects:
            if 'proxy' in mesh.name:
                continue
                main_object_name = mesh.name.split('_proxy')[0]
                main_object = get_object(main_object_name)
                mesh["source_path"] = main_object["source_path"]

            if 'bndl' in mesh.name:
                bundles_items.append(mesh)
                continue

            clean_name = mesh.name.split(":")

            if len(clean_name) > 1:
                mesh_name = clean_name[0]
            else:
                mesh_name = clean_name[0]

            if clean_name[1] == 'rig':
                rig_items.append(mesh)
                rigs[mesh_name] = rig.get_msd_info(mesh)
                continue

            if clean_name[1] == 'cam':
                rig_items.append(mesh)
                cameras[mesh_name] = cam.get_msd_info(mesh)
                continue


            print(10 * '_*')
            print(mesh_name)
            meshes[mesh_name] = mdl.get_msd_info(mesh)

        for bundle in bundles_items:
            each_bundle = {}
            each_bundle['meshes'] = {}
            for mesh in bundle.children:
                clean_name = mesh.name.split(":")
                if len(clean_name) > 1:
                    clean_name = clean_name[0]
                else:
                    clean_name = clean_name[0]
                print(10 * '_*')
                print(clean_name)
                each_bundle['meshes'][clean_name] = mdl.get_msd_info(mesh)
                each_bundle['source_path'] =  bundle['source_path']
            bundles[bundle.name] = each_bundle


        meshes_dict['attrs'] = {**{'meshes': meshes},**{'bundles': bundles},**{'rigs':rigs},**{'cameras':cameras}}


        meshes_dict['source_path'] = scene_object().path

        return meshes_dict
    def export_msd(self, task_name = None, selected=None):
        """

        """
        if not selected:
            print(self.path_object.msd_path)
            self.path_object.save_msd(self.get_msd_info(task_name))
            # update the project.msd
            # update the project_test.msd


def get_latest(ext='msd'):
    this_obj = scene_object().copy(task=TASKNAME, context='render',
                                   user='publish', latest=True, set_proper_filename=True, ext=ext)
    return this_obj

def get_namespace(filepath):
    from cgl.plugins.blender.utils import get_next_namespace, read_matrix, parent_object, create_object

    namespace = ''
    path_object = PathObject(filepath)
    if path_object.task == 'cam':
        namespace = 'cam'
    elif path_object.scope == 'assets':
        namespace = path_object.shot
    elif path_object.scope == 'shots':
        namespace = 'tempNS'
    return get_next_namespace(namespace)



def import_mdl(mesh,reference = True, latest = True, bundle = None,parent = None):
    from pprint import pprint
    from cgl.core.config.config import ProjectConfig
    from cgl.plugins.blender.utils import get_next_namespace, read_matrix, parent_object, create_object
    from cgl.plugins.blender.alchemy import  reference_file, import_file
    from cgl.plugins.blender.msd import set_matrix
    from .anim import make_proxy
    from ..msd import path_object_from_source_path, tag_object
    import bpy
    relative_path = mesh['source_path']
    d2 = path_object_from_source_path(relative_path)
    ns2 = d2.shot
    if latest:
        d2 = d2.latest_version(publish_=True)

    task = d2.task
    transforms = mesh['transform']['matrix'].split(' ')
    float_transforms = [float(x) for x in transforms]

    if reference == True:

        ref = reference_file(namespace=ns2, filepath=d2.path_root)


    else:
        print('_'*8,'IMPORTING FILES','_'*8)
        print(d2.path_root)
        if task == 'rig':
            return
        ref = import_file(namespace=ns2, filepath=d2.path_root)


    set_matrix(ref, float_transforms)

    layout = create_object('{}_{}:lay'.format(scene_object().seq, scene_object().asset))
    group = create_object('{}_{}:{}'.format(scene_object().seq, scene_object().asset,mesh['layer']), parent=layout)
    parent_object(ref,group)
    if bundle:
        tag_object(ref, tag  = 'bundle', value = bundle)

def import_rig(rig_dictionary,reference = True, latest = True):
    from pprint import pprint
    from cgl.core.config.config import ProjectConfig
    from cgl.plugins.blender.utils import get_next_namespace, read_matrix, parent_object, create_object,get_object
    from cgl.plugins.blender.alchemy import  reference_file, import_file
    from cgl.plugins.blender.msd import set_matrix
    from .anim import make_proxy
    from ..msd import path_object_from_source_path
    import bpy


    relative_path = rig_dictionary['source_path']
    path_object = path_object_from_source_path(relative_path)
    ns2 = path_object.shot
    if latest:
        path_object = path_object.latest_version(publish_=True)

    task = path_object.task
    transforms = rig_dictionary['transform']['matrix'].split(' ')
    float_transforms = [float(x) for x in transforms]

    if reference == True:

        ref = reference_file(namespace=ns2, filepath=path_object.path_root)
        layout_group = create_object(('{}_{}:FG'.format(scene_object().seq, scene_object().asset)))
        parent_object(child=ref, parent=layout_group)

        print('________IMPORTING RIG_____________')
        rig = make_proxy(path_object, ref)
        rig_root = rig_dictionary['main_controller']
        proxy = bpy.data.objects['{}:rig_proxy'.format(ns2)]
        ref = proxy.pose.bones[rig_root]


    else:


        if task == 'rig':
            return
        ref = import_file(namespace=ns2, filepath=path_object.path_root)

    layout = create_object('{}_{}:lay'.format(scene_object().seq, scene_object().asset))
    group = create_object('{}_{}:{}'.format(scene_object().seq, scene_object().asset, rig_dictionary['layer']), parent=layout)
    set_matrix(ref, float_transforms)
    parent_object(get_object('{}:rig_proxy'.format(path_object.asset)), group)


def main_import(filepath= None ,reference = True, latest = False ,parent=None,**kwargs):
    """

    :param filepath:
    :return:
    """
    from pprint import pprint
    from cgl.core.config.config import ProjectConfig
    from cgl.plugins.blender.utils import get_next_namespace, read_matrix, parent_object, create_object
    from cgl.plugins.blender.alchemy import  reference_file, import_file
    from cgl.plugins.blender.msd import set_matrix
    from .anim import make_proxy
    from ..msd import path_object_from_source_path
    import bpy


    if filepath == None:
        filepath = scene_object().copy(task = 'lay', latest= True,user = 'publish').path_root


    d = PathObject(filepath)
    layout_data = d.msd_info

    meshes = layout_data['attrs']['meshes']
    rigs = layout_data['attrs']['rigs']
    bundles = layout_data['attrs']['bundles']

    for mesh in meshes:
        dict = meshes[mesh]
        import_mdl(dict,reference = reference,latest = latest)

    for rig in layout_data['attrs']['rigs']:

        dict = rigs[rig]
        import_rig(dict)

    for bundle in bundles:
        print('_' * 5, bundle)
        print('_' * 8, 'BUNDLES', '_' * 8)
        meshes = bundles[bundle]['meshes']
        for mesh in meshes:
            bndl_source= bundles[bundle]['source_path']

            import_mdl(meshes[mesh],
                       reference = reference,
                       latest = latest,
                       bundle = bndl_source,
                       parent =  meshes[mesh]['layer'])



def check_reference_attribute(attribute,reference_path = None):
    from cgl.plugins.blender.alchemy import scene_object,PathObject, set_relative_paths
    set_relative_paths(False)
    failed_libraries = []

    if not reference_path:
        reference_path = scene_object()

    attrib_check = eval('reference_path.{}'.format(attribute))

    for library in bpy.data.libraries:
        path_object = PathObject(library.filepath)
        lib_attribute = eval('path_object.{}'.format(attribute))
        if not lib_attribute == attrib_check:
            new_filepath = eval("path_object.copy(attibute=attrib_check).path_root")
            library.filepath = new_filepath
            library.reload()

    for library in bpy.data.libraries:
        path_object = PathObject(library.filepath)
        lib_attribute = eval('path_object.{}'.format(attribute))
        if not lib_attribute == attrib_check:
            failed_libraries.append(path_object.filename)

    set_relative_paths(True)

    return failed_libraries
