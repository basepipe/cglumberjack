import os
import copy
import glob
import pymel.core as pm
import cgl.plugins.MagicSceneDescription as msd
reload(msd)
from cgl.core.config import app_config
from cgl.core.utils.read_write import load_json, save_json
from cgl.plugins.maya.lumbermill import get_scene_name, LumberObject

CONFIG = app_config()


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

    def load_description_classes(self):
        self.ad_class = AssetDescription

    def set_scene_file(self):
        """
        sets the scene file as path_root for the msd
        :return:
        """
        self.scene_file = get_scene_name()
        self.path_object = LumberObject(self.scene_file)
        pass

    @staticmethod
    def get_assets(ignore=[]):
        meshes = []
        references = pm.listReferences()
        for ref in references:
            if ref not in ignore:
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
        sel = pm.ls(type='transform')
        for obj in sel:
            if obj.hasAttr('BundlePath'):
                bundles.append(obj)
        if children:
            for b in bundles:
                children = pm.listRelatives(b, ad=True)
                for child in children:
                    try:
                        ref = pm.referenceQuery(child, filename=True, wcn=True)
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
        self.mesh_name = mesh_name
        self.data = CONFIG['layout']['asset']
        self.asset_type = asset_type
        if not mesh_object:
            self.mesh_object = self.get_object_from_mesh_name()
        else:
            self.mesh_object = mesh_object
        if not self.mesh_name:
            self.get_mesh_name_from_object()
        self.create_msd()

    def create_msd(self):
        self.get_asset_name()
        self.get_asset_path()
        self.create_asset_description()

    def get_object_from_mesh_name(self):
        return pm.PyNode(self.mesh_name)

    def get_asset_path(self):
        """
        get the published path of the asset we're creating a description for
        :return:
        """
        try:
            self.path_root = self.mesh_object.path
        except AttributeError:
            self.path_root = pm.getAttr(self.mesh_object.BundlePath)
        self.path_object = LumberObject(self.path_root)

    def get_mesh_name_from_object(self):
        """
        get the mesh name (name of asset in scene) from the mesh_object
        :return:
        """
        self.mesh_name = self.mesh_object.nodes()[0]

    def get_asset_name(self):
        """
        get the unique asset name that will be used in the dictionary - this must be unique.
        :return:
        """
        self.asset_name = self.mesh_name.namespace()[:-1]

    def get_transform_arrays(self):

        translate = pm.getAttr('%s.t' % self.mesh_name)
        scale = pm.getAttr('%s.s' % self.mesh_name)
        rotate = pm.getAttr('%s.r' % self.mesh_name)
        t_array = [translate[0], translate[1], translate[2]]
        r_array = [rotate[0], rotate[1], rotate[2]]
        s_array = [scale[0], scale[1], scale[2]]
        return t_array, r_array, s_array

    def get_matrix(self, query=False):
        """
        Returns a matrix of values relating to translate, scale, rotate.
        :param obj:
        :param query:
        :return:
        """
        obj = self.mesh_name
        if not query:
            if pm.objExists(obj):
                if 'rig' in obj:
                    translate = '%s:translate' % obj.split(':')[0]
                    scale = '%s:scale' % obj.split(':')[0]
                    rotate = '%s:rotate' % obj.split(':')[0]
                    relatives = pm.listRelatives(obj)
                    if translate and scale in relatives:
                        if rotate in pm.listRelatives(translate):
                            matrix_rotate = pm.getAttr('%s.matrix' % rotate)[0:3]
                            matrix_scale = pm.getAttr('%s.matrix' % scale)[0:3]
                            matrix = matrix_scale * matrix_rotate
                            matrix.append(pm.getAttr('%s.matrix' % translate)[3])
                        else:
                            attr = "%s.%s" % (obj, 'matrix')
                            if pm.attributeQuery('matrix', n=obj, ex=True):
                                matrix = pm.getAttr(attr)
                            else:
                                matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0],
                                          [0.0, 0.0, 0.0, 1.0]]
                    else:
                        attr = "%s.%s" % (obj, 'matrix')
                        if pm.attributeQuery('matrix', n=obj, ex=True):
                            matrix = pm.getAttr(attr)
                        else:
                            matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
                                      [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
                else:
                    attr = "%s.%s" % (obj, 'matrix')
                    if pm.attributeQuery('matrix', n=obj, ex=True):
                        matrix = pm.getAttr(attr)
                    else:
                        matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0],
                                  [0.0, 0.0, 0.0, 1.0]]
            else:
                matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
            return matrix
        else:
            return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

    def create_asset_description(self):
        """
        creates the asset description for the object.
        :return:
        """
        self.add_matching_files_to_dict(self.path_object.copy(context='render').path_root, self.data)
        self.set_path_object_details()
        matrix = self.get_matrix()
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


class CameraDescription(AssetDescription):

    def __init__(self, name, start_frame=0, end_frame=0, start_handle=None, end_handle=None):
        self.name = name

    def set_frame_range(self, start_frame, end_frame, start_handle, end_handle):
        pass


def set_matrix(mesh, matrix=None):
    """
    Sets translate, rotate, scale values according to matrix value given
    :param mesh:
    :param matrix:
    :return:
    """
    r_matrix = []
    if not matrix:
        matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    for manip in matrix:
        for val in manip:
            r_matrix.append(val)
    if pm.objExists(mesh):
        pm.xform(mesh, m=r_matrix)


