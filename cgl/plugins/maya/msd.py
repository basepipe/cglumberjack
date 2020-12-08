import os
import copy
import glob
import pymel.core as pm
import cgl.plugins.MagicSceneDescription as msd
reload(msd)
from cgl.core.config import app_config
from cgl.core.utils.read_write import load_json, save_json
from cgl.plugins.maya.lumbermill import get_scene_name, LumberObject, scene_object
from cgl.plugins.maya.utils import load_plugin, select_reference

CONFIG = app_config()


class MagicSceneDescription(msd.MagicSceneDescription):

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
        print(ignore)
        meshes = []
        references = pm.listReferences()
        for ref in references:
            print(ref)
            if ref not in ignore:
                meshes.append(ref)
        return meshes

    def get_anim(self):
        ref_paths = []
        if pm.objExists('ANIM'):
            anim_nodes = pm.listRelatives('ANIM', children=True)
            for a in anim_nodes:
                ref_paths.append(pm.referenceQuery(a, filename=True))
            return anim_nodes, ref_paths
        else:
            return []

    @staticmethod
    def get_cameras(force_naming=True):
        return None

    @staticmethod
    def get_lights():
        pass

    @staticmethod
    def get_cameras():
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
        if self.asset_type == 'asset':
            self.path_root = self.mesh_object.path
        elif self.asset_type == 'bndl':
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
        # see if it's animated (is it in the ANIM group)
        if self.asset_type == 'asset':
            self.add_matching_files_to_dict(self.path_object.copy(context='render').path_root, self.data)
        elif self.asset_type == 'anim':
            anim_obj = LumberObject(pm.referenceQuery(self.mesh_object, filename=True))
            filename = '{}_{}*'.format(anim_obj.seq, anim_obj.shot)
            filepath = self.path_object.copy(context='render', filename=filename).path_root
            self.add_matching_files_to_dict(filepath, self.data)
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
        files = glob.glob('{}*'.format(no_ext_path))
        for f in files:
            for i in ignore:
                if i not in f:
                    _, ext = os.path.splitext(f)
                    ext = ext.replace('.', '')
                    dictionary[ext] = copy.copy(remove_root(f))

    def set_path_object_details(self):
        self.data['name'] = self.path_object.shot
        self.data['source_path'] = self.path_object.path
        self.data['task'] = self.path_object.task

    def export(self):
        """
        exports the camera dict to
        :return:
        """
        print('Exporting .msd to: {}'.format(self.path_root))
        save_json(self.path_root, self.data)


class CameraDescription(AssetDescription):

    def __init__(self, mesh_name, start_frame=0, end_frame=0, handle_start=None, handle_end=None,
                 add_to_msd=None):
        """

        :param name:
        :param start_frame:
        :param end_frame:
        :param handle_start:
        :param handle_end:
        :param add_to_msd:
        """

        self.mesh_name = mesh_name
        self.data = CONFIG['layout']['asset']
        self.asset_type = 'camera'
        self.mesh_object = self.get_object_from_mesh_name()
        self.create_msd()

        if start_frame:
            self.start_frame = start_frame
        else:
            self.start_frame = int(pm.playbackOptions(query=True, animationStartTime=True))
        if end_frame:
            self.end_frame = end_frame
        else:
            self.end_frame = int(pm.playbackOptions(query=True, animationEndTime=True))
        if handle_start:
            self.handle_start = handle_start
        else:
            self.handle_start = int(pm.playbackOptions(query=True, min=True))
        if handle_end:
            self.handle_end = handle_end
        else:
            self.handle_end = int(pm.playbackOptions(query=True, max=True))
        self.set_frame_range()
        self.add_matching_files_to_dict(self.path_object.path_root, self.data)

    def set_path_object_details(self):
        self.data['name'] = self.mesh_name
        self.data['source_path'] = scene_object().path
        self.data['task'] = 'cam'

    def get_asset_path(self):
        """

        :return:
        """
        from cgl.plugins.maya.tasks.cam import get_latest
        seq, shot = self.mesh_name.split('_')
        seq = seq.replace('cam', '')
        self.path_object = get_latest(seq, shot).copy(ext='msd')
        self.path_root = self.path_object.path_root

    def set_frame_range(self, ):

        self.data['start_frame'] = self.start_frame
        self.data['end_frame'] = self.end_frame
        self.data['handle_start'] = self.handle_start
        self.data['handle_end'] = self.handle_end
        pass

    def get_asset_name(self):
        """
        get the unique asset name that will be used in the dictionary - this must be unique.
        :return:
        """
        self.asset_name = self.mesh_name


def load_msd(msd_path):
    pm.select(d=True)
    import cgl.plugins.maya.lumbermill as lumbermill
    reload(lumbermill)
    msd_ = load_json(msd_path)
    for asset in msd_:
        namespace = asset
        if msd_[asset]['type'] == 'anim':
            load_plugin('AbcImport')
            if not pm.objExists('ANIM'):
                group = pm.group(name='ANIM')
            else:
                group = 'ANIM'
            pm.select(d=True)
            reference_path = "%s%s" % (app_config()['paths']['root'], msd_[asset]['abc'])
        elif msd_[asset]['type'] == 'asset':
            if not pm.objExists('LAYOUT'):
                group = pm.group(name='LAYOUT')
            else:
                group = 'LAYOUT'
            reference_path = "%s%s" % (app_config()['paths']['root'], msd_[asset]['mb'])
        elif msd_[asset]['type'] == 'camera':
            if not pm.objExists('CAMERA'):
                group = pm.group(name='CAMERA')
            else:
                group = 'CAMERA'
            reference_path = "%s%s" % (app_config()['paths']['root'], msd_[asset]['mb'])
        reference_path = reference_path.replace('\\', '/')
        ref = lumbermill.reference_file(reference_path, namespace=namespace)
        ref_node = select_reference(ref)
        pm.select(d=True)
        pm.parent(ref_node, group)
        pm.select(d=True)


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


