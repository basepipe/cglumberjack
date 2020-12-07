import os
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.maya.lumbermill import LumberObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.core.assetcore as assetcore
import bpy
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


def write_layout(outFile=None):
    """

    :param outFile:
    :return:
    """
    from cgl.plugins.blender.lumbermill import scene_object, LumberObject
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
                    libObject = LumberObject(filename)

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
    from cgl.plugins.blender.lumbermill import scene_object, LumberObject, import_file_old
    from cgl.core.utils.read_write import load_json
    import bpy

    bpy.ops.file.make_paths_absolute()
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
        lumberObject = LumberObject(pathToFile)

        if lumberObject.filename_base in bpy.data.libraries:
            lib = bpy.data.libraries[lumberObject.filename]
            bpy.data.batch_remove(ids=([lib]))
            import_file_old(lumberObject.path_root, linked=linked, append=append)
        else:
            import_file_old(lumberObject.path_root, linked=linked, append=append)

        if p not in bpy.data.objects:
            obj = bpy.data.objects.new(p, None)
            bpy.context.collection.objects.link(obj)
            obj.instance_type = 'COLLECTION'
            obj.instance_collection = bpy.data.collections[lumberObject.asset]

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


