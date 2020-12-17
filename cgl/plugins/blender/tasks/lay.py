import os
import glob
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.blender.alchemy import PathObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.core.assetcore as assetcore
import bpy


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
        from cgl.plugins.blender.alchemy import  set_relative_paths
        main_import(filepath)
        set_relative_paths(True)

    def build(self):
        from cgl.plugins.blender.utils import create_shot_mask_info,set_collection_name
        create_shot_mask_info()
        set_collection_name()


    def import_latest(self, seq=None, shot= None):
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
        print(scene_object().path_root)
        print(scene_object().shot)
        print(layout_obj.path_root)
        for each in glob.glob(layout_obj.path_root):
            if '.msd' in each:
                layout_path = each
        if layout_path:
            self._import(filepath=layout_path)
        else:
            print('Could not glob layout path at {}'.format(layout_obj.path))


def get_latest(ext='msd'):
    this_obj = scene_object().copy(task=TASKNAME, context='render',
                                   user='publish', latest=True, set_proper_filename=True, ext=ext)
    return this_obj


def main_import(filepath):
    """

    :param filepath:
    :return:
    """
    from pprint import pprint
    from cgl.core.config import app_config
    from cgl.plugins.blender.utils import get_next_namespace, read_matrix, parent_object, create_object
    from cgl.plugins.blender.alchemy import  reference_file
    from cgl.plugins.blender.msd import set_matrix
    from .anim import make_proxy
    import bpy
    relative_path = None
    root = app_config()['paths']['root']
    d = PathObject(filepath)

    layout_data = load_json(filepath)
    group = create_object('{}:lay'.format(scene_object().asset))
    pprint(layout_data)
    for each in layout_data:
        if 'source_path' in layout_data[each]:
            # this is a bundle, rather than a layout - unsure why this has changed so drastically
            # TODO - look at what's going on here.
            relative_path = layout_data[each]['source_path']
            task = layout_data[each]['task']
            transforms = layout_data[each]['transform'].split(' ')
        company = scene_object().company

        if root not in relative_path:

            reference_path = "%s\%s" % (root, relative_path)
        else:
            reference_path = relative_path
        float_transforms = [float(x) for x in transforms]

        d2 = PathObject(reference_path)
        ns2 = get_next_namespace(d2.shot)
        print(ns2)
        ref = reference_file(namespace=ns2, filepath=reference_path)


        if task == 'rig':
            rig = make_proxy(d2, ref)
            rig_root = layout_data[each]['rig_root']
            ref = rig.pose.bones[rig_root]

        set_matrix(ref, float_transforms)

        #parent_object(ref, group)


def write_layout(outFile=None):
    """

    :param outFile:
    :return:
    """
    from cgl.plugins.blender.lumbermill import scene_object, PathObject
    from cgl.core.utils.read_write import save_json
    import bpy
    from pathlib import Path

    if outFile == None:
        outFile = scene_object().copy(ext='json', task='lay', user='publish').path_root
    data = {}

    for obj in bpy.context.view_layer.objects:
        if obj.is_instancer:
            print(5 * '_' + obj.name + 5 * '_')
            name = obj.name
            #            blender_transform = np.array(obj.matrix_world).tolist()
            blender_transform = [obj.matrix_world.to_translation().x,
                                 obj.matrix_world.to_translation().y,
                                 obj.matrix_world.to_translation().z,
                                 obj.matrix_world.to_euler().x,
                                 obj.matrix_world.to_euler().y,
                                 obj.matrix_world.to_euler().z,
                                 obj.matrix_world.to_scale().x,
                                 obj.matrix_world.to_scale().y,
                                 obj.matrix_world.to_scale().z]

            instanced_collection = obj.instance_collection
            if instanced_collection:
                collection_library = return_linked_library(instanced_collection.name)

                if collection_library:

                    libraryPath = bpy.path.abspath(collection_library.filepath)
                    filename = Path(bpy.path.abspath(libraryPath)).__str__()
                    libObject = PathObject(filename)

                    data[name] = {'name': libObject.asset,
                                  'source_path': libObject.path,
                                  'blender_transform': blender_transform}
                else:
                    print('{} has no instanced collection'.format(obj.name))

            else:
                print('{} has no instanced collection'.format(obj.name))

    save_json(outFile, data)

    return (outFile)


def read_layout(outFile=None, linked=False, append=False):
    """
    Reads layout from json file
    :param outFile: path to json file
    :param linked:
    :param append:
    :return:
    """
    from cgl.plugins.blender.alchemy import scene_object, PathObject, import_file_old,reference_file
    from cgl.core.utils.read_write import load_json
    from cgl.plugins.blender.alchemy import set_relative_paths
    import bpy

    set_relative_paths(False)

    if outFile == None:
        outFileObject = scene_object().copy(ext='json', task='lay', set_proper_filename=True).latest_version()
        outFile = outFileObject.path_root

    data = load_json(outFile)

    for p in sorted(data):
        print(p)
        data_path = data[p]['source_path']
        blender_transform = data[p]['blender_transform']

        transform_data = []
        for value in blender_transform:
            transform_data.append(float(value))

        pathToFile = os.path.join(scene_object().root, data_path)
        PathObject = PathObject(pathToFile)

        if PathObject.filename_base in bpy.data.libraries:
            lib = bpy.data.libraries[PathObject.filename]
            bpy.data.batch_remove(ids=([lib]))


        reference_file(PathObject.path_root)

        print(5555555555555555555555555)
        if p not in bpy.data.objects:
            obj = bpy.data.objects.new(p, None)
            bpy.context.collection.objects.link(obj)
            obj.instance_type = 'COLLECTION'
            obj.instance_collection = bpy.data.collections[PathObject.asset]

            print(222222222222222222222222)
            print(data[p]['task'])
            if data[p]['task'] == 'rig':
                obj = make_proxy(PathObject,obj)


            location = (transform_data[0], transform_data[1], transform_data[2])
            obj.location = location

            rotation = (transform_data[3], transform_data[4], transform_data[5])
            obj.rotation_euler = rotation

            scale = (transform_data[6], transform_data[7], transform_data[8])
            obj.scale = scale


        else:

            obj = bpy.data.objects[p]
            print('updating position')
            print(obj.name)

            location = (transform_data[0], transform_data[1], transform_data[2])
            obj.location = location

            rotation = (transform_data[3], transform_data[4], transform_data[5])
            obj.rotation_euler = rotation

            scale = (transform_data[6], transform_data[7], transform_data[8])
            obj.scale = scale

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
