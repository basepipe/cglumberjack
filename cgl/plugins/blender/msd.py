import bpy

import os
import copy
import glob
import importlib
from cgl.core.config.config import ProjectConfig
from cgl.core.utils.read_write import load_json, save_json
import cgl.plugins.MagicSceneDescription as msd
importlib.reload(msd)
import bpy
from cgl.plugins.blender.alchemy import get_scene_name,scene_object

from cgl.core.path import PathObject
CONFIG = ProjectConfig().project_config



class MagicSceneDescription(msd.MagicSceneDescription):
    scene_object = None
    path = None
    scene_file = None
    path_object = None
    data = {}
    ad_class = None
    lgt_class = None

    def __init__(self):
        """

        :param software:
        :param type_:
        :param scene_description_path:
        """
        self.create_msd()


    def set_scene_data(self):
        """
        sets self.data with all information about the scene, this is
        :return:
        """
        bundles, children = self.get_bundles(children=True)
        if bundles:
            for b in bundles:
                b_desc = self.ad_class(b, asset_type='bndl')
                self.add_asset(b_desc)
        assets = self.get_assets(ignore=[])
        if assets:
            for a in assets:
                print(333333)
                print('________________{}'.format(a))
                a_desc = self.ad_class(mesh_object=a)
                print(a_desc.data)
                self.add_asset(a_desc)

    def load_description_classes(self):
        self.ad_class = AssetDescription

    def set_scene_file(self):
        """
        sets the scene file as path_root for the msd
        :return:
        """
        self.scene_file = get_scene_name()
        self.path_object = PathObject(self.scene_file)
        pass

    def get_ref_from_object(self,object):
        if not object.is_instancer:
            object = bpy.data.object[return_asset_name(object)]
        library = object.instance_collection.library

        return (library)

    @staticmethod
    def get_assets(ignore=[]):
        meshes = []
        references = []
        for obj in bpy.data.objects:
            if obj.is_instancer == True:
                references.append(obj)


        for ref in references:

            meshes.append(ref)

        return meshes

    @staticmethod
    def get_cameras(force_naming=True):
        return None

    @staticmethod
    def get_lights(self):
        pass

    @staticmethod
    def get_bundles(children=False):
        """
        gets all the bundles in the scene
        :param children: if True it returns children as a seperate list.
        :return:
        """
        bundles = []
        bundle_ref_children = []
        sel = bpy.data.objects

        for obj in sel:
            if 'BundlePath' in obj.keys():
                bundles.append(obj)
        if children:
            for b in bundles:
                children = b.children
                for child in children:
                    try:
                        ref = get_ref_from_object(child)
                        bundle_ref_children.append(ref)
                    except RuntimeError:
                        logging.info('%s is not a reference' % child)
            return bundles, bundle_ref_children
        else:
            return bundles

class AssetDescription(object):
    name = None
    namespace = ''
    data = {}
    path_root = None
    asset_name = ''
    path_object = None
    object_type = None

    def __init__(self, mesh_name=None, mesh_object=None, selected=False, asset_type='asset'):
        self.mesh_name = None
        self.data = CONFIG['layout']['asset']
        self.asset_type = asset_type
        if not mesh_object:
            self.mesh_object = self.get_object_from_mesh_name()
        else:
            self.mesh_object = mesh_object
        if not self.mesh_name:
            self.mesh_name = self.mesh_object.name

        self.create_msd()

    def create_msd(self):
        self.get_asset_name()
        self.get_asset_path()
        self.create_asset_description()

    def get_object_from_mesh_name(self):
        return bpy.data.objects[self.mesh_name]

    def get_asset_path(self):
        import os
        """
        get the published path of the asset we're creating a description for
        :return:
        """
        try:
            self.path_root = self.mesh_object['source_path']
        except (AttributeError,KeyError):
            print('no source_path found in {}'.format(self.mesh_object))
            pass

        self.path_object = PathObject(os.path.join(scene_object().root,self.path_root))

        print(self.path_object.path_root)

    def get_mesh_name_from_object(self):
        """
        get the mesh name (name of asset in scene) from the mesh_object
        :return:
        """
        self.mesh_name = self.mesh_object.name

    def get_asset_name(self):
        """
        get the unique asset name that will be used in the dictionary - this must be unique.
        :return:
        """
        self.asset_name = self.mesh_name.split(':')[0]

    def assign_bundlePath():
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                if obj.is_instancer:
                    lib = get_lib_from_object(obj)
                    if lib:
                        obj['BundlePath'] = return_lib_path(lib)
                    else:
                        obj['BundlePath'] = 'NOT BUNDLED'

    def get_transform_arrays(self):

        """
         convenience function, it gets all the transfors (translate, rotate, scale) as seperate entities
         so we can add that to the scene description, it can be convenient to have in some 3d packages.
         :param obj: object to find transform arrays for
         :return: translate, rotate, scale arrays
         """

        translate = self.mesh_object.matrix_world.to_translation()
        scale = self.mesh_object.matrix_world.to_scale()
        rotate = self.mesh_object.matrix_world.to_euler()
        t_array = [translate[0], translate[1], translate[2]]
        r_array = [rotate[0], rotate[1], rotate[2]]
        s_array = [scale[0], scale[1], scale[2]]
        return t_array, r_array, s_array

    def get_matrix(self, obj=None, query=False,rig_root = 'c_pos'):
        from cgl.plugins.blender.utils import get_object
        """
        Returns a matrix of values relating to translate, scale, rotate.
        :param obj:
        :param query:
        :return:
        """
        from cgl.plugins.blender.alchemy import PathObject

        if not query:
            #TODO: check with tom distinction on rig objects.
            root = app_config()['paths']['root']
            source_path = obj['source_path']
            reference_path = "%s\%s" % (root, source_path)
            path_root = PathObject(reference_path)
            object = get_object(obj)
            if object:

                obj_matrix = obj.matrix_world
                if path_root.task == 'rig':
                    proxy = bpy.data.objects['{}_proxy'.format(obj.name)]
                    obj_matrix = proxy.pose.bones[rig_root].matrix_basis


                attr = "%s.%s".format(obj, 'matrix')

                matrix = [[obj_matrix.to_translation().x,
                           obj_matrix.to_translation().y,
                           obj_matrix.to_translation().z],
                          [obj_matrix.to_euler().x,
                           obj_matrix.to_euler().y,
                           obj_matrix.to_euler().z],
                          [obj_matrix.to_scale().x,
                           obj_matrix.to_scale().y,
                           obj_matrix.to_scale().z]]
        #
            else:
                matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
            return matrix
        else:
            print('NO OBJECT _____________')
            return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

    def create_asset_description(self):
        """
        creates the asset description for the object.
        :return:
        """
        self.add_matching_files_to_dict(self.path_object.copy(context='render').path_root, self.data)
        self.set_path_object_details()
        objectName = '{}:{}'.format(self.data['name'],self.data['task'])
        matrix = self.get_matrix(bpy.data.objects[objectName])
        matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
        translate, rotate, scale = self.get_transform_arrays()
        self.data['transform'] = matrix
        self.data['type'] = self.asset_type
        self.data['translate'] = [translate[0], translate[1], translate[2]]
        self.data['rotate'] = [rotate[0], rotate[1], rotate[2]]
        self.data['scale'] = [scale[0], scale[1], scale[2]]

    @staticmethod
    def add_matching_files_to_dict(file_path, dictionary):
        """
        adds file that match filepath.* to the dictionary, this is useful when there are multiple file types
        for the same asset as with a model file that has .mb, .ma, .obj, .blend, etc...
        :param file_path:
        :param dictionary:
        :return:
        """
        from cgl.core.path import remove_root
        ignore = ['.json']
        no_ext_path, ext = os.path.splitext(file_path)
        print('globbing {}'.format(no_ext_path))
        files = glob.glob('{}*'.format(no_ext_path))
        for f in files:
            for i in ignore:
                if i not in f:
                    _, ext = os.path.splitext(f)
                    ext = ext.replace('.', '')
                    dictionary[ext] = remove_root(f)

    def set_path_object_details(self):
        self.data['name'] = self.path_object.shot
        self.data['source_path'] = self.path_object.path
        self.data['task'] = self.path_object.task
        if self.path_object.task == 'rig':

            self.data['rig_root'] = 'c_pos' #TODO this sholdn't be hardcoded move to globals

class CameraDescription(AssetDescription):

    def __init__(self, name, start_frame=0, end_frame=0, start_handle=None, end_handle=None):
        self.name = name

    def set_frame_range(self, start_frame, end_frame, start_handle, end_handle):
        pass

def path_object_from_source_path(source_path):
    from cgl.core.config.config import ProjectConfig
    from cgl.plugins.blender.alchemy import PathObject
    root = ProjectConfig().root_folder
    if root not in source_path:
        reference_path = "%s\%s" % (root, source_path)
    else:
        reference_path = source_path


    path_object = PathObject(reference_path)
    return path_object

def path_object_from_asset_name(asset_name ,task = 'mdl', seq = 'char'):
    from cgl.core.config.config import ProjectConfig
    from cgl.plugins.blender.alchemy import PathObject
    root = ProjectConfig().root_folder

    path_object = scene_object().copy(scope ='assets',
                                      context = 'source',
                                      asset = asset_name,
                                      task = task,
                                      latest=True,
                                      user = 'publish',
                                      set_proper_filename=True,
                                      seq = seq)

    return path_object

def set_matrix(obj, transform_data):
    """
    Sets translate, rotate, scale values according to matrix value given
    :param mesh:
    :param matrix:
    :return:
    """
    r_matrix = []


    location = (transform_data[0], transform_data[1], transform_data[2])
    obj.location = location

    rotation = (transform_data[3], transform_data[4], transform_data[5])
    obj.rotation_euler = rotation

    scale = (transform_data[6], transform_data[7], transform_data[8])
    obj.scale = scale


def tag_object(objects, tag, value):
    if type(objects) == list:

        for obj in objects:
            obj[tag] = value

    else:
        objects[tag] = value

def switch_layer_visibility(objects = None, tag= 'rig_layer', layer='SECONDARY'):


    import bpy
    from cgl.plugins.blender.tasks.mdl import get_mdl_objects

    if objects == None:
        objects = get_mdl_objects()

    current_scene = bpy.context.scene
    if layer in current_scene.keys():

        current_scene[layer] = not current_scene[layer]
    else:
        current_scene[layer] = True

    for obj in objects:
        if obj[0][tag] == layer:
            print(obj[0])
            obj[0].hide_viewport = current_scene[layer]


def add_namespace(obj=None, namespace=None, ):
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.plugins.blender.utils import get_object, get_objects_in_hirarchy

    if obj == None:
        obj = 'mdl'

    if namespace == None:
        namespace = scene_object().asset

    for obj in get_objects_in_hirarchy(obj=get_object(obj)):
        object = get_object(obj)
        object.name = '{}:{}'.format(namespace, object.name)


def remove_namespace(obj = None,namespace=None):
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.plugins.blender.utils import get_object, get_objects_in_hirarchy
    if namespace == None:
        namespace = scene_object().asset
    if obj == None:
        obj = '{}:mdl'.format(namespace)

    for obj in get_objects_in_hirarchy(obj=get_object(obj)):
        object = get_object(obj)
        object.name = object.name.split(':')[1]



