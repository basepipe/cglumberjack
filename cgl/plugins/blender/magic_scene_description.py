import os
import copy
import glob
from cgl.plugins.blender.alchemy import scene_object, objExists
from cgl.core.path import PathObject
import cgl.core.assetcore as assetcore
from cgl.core.config import app_config
from cgl.core.utils.read_write import load_json, save_json

CONFIG = app_config()


def create_asset_description(ref):
    """
    Creates the asset dictionary for a layout or bundle, assumes it's being handed a reference
    :param ref:
    :param
    :return:
    """
    asset_dict = CONFIG['layout']['asset']

    top_node = ref

    print(ref['BundlePath'])
    ref_obj = PathObject(ref['BundlePath'])

    add_matching_files(ref['BundlePath'], asset_dict)

    matrix = get_matrix(ref)
    matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
    namespace = ref_obj.asset
    translate, scale, rotate = get_transform_arrays(top_node)
    asset_dict['name'] = ref_obj.shot
    asset_dict['source_path'] = ref_obj.path
    asset_dict['task'] = ref_obj.task
    asset_dict['transform'] = matrix
    asset_dict['type'] = 'asset'
    asset_dict['translate'] = [translate[0], translate[1], translate[2]]
    asset_dict['rotate'] = [rotate[0], rotate[1], rotate[2]]
    asset_dict['scale'] = [scale[0], scale[1], scale[2]]
    print(asset_dict)
    return namespace, asset_dict


def add_matching_files(filepath, dictionary):
    """
    adds file that match filepath.* to the dictionary
    :param filepath:
    :param dictionary:
    :return:
    """
    import importlib

    import cgl.core.path as path
    importlib.reload(path)
    ignore = ['.json']
    no_ext_path, ext = os.path.splitext(filepath)
    files = glob.glob('{}*'.format(no_ext_path))
    for f in files:
        for i in ignore:
            if i not in f:
                _, ext = os.path.splitext(f)
                ext = ext.replace('.', '')
                dictionary[ext] = path.remove_root(f)


def get_transform_arrays(obj):
    """
    convenience function, it gets all the transfors (translate, rotate, scale) as seperate entities
    so we can add that to the scene description, it can be convenient to have in some 3d packages.
    :param obj: object to find transform arrays for
    :return: translate, rotate, scale arrays
    """

    translate = obj.matrix_world.to_translation()
    scale = obj.matrix_world.to_scale()
    rotate = obj.matrix_world.to_euler()
    t_array = [translate[0], translate[1], translate[2]]
    r_array = [rotate[0], rotate[1], rotate[2]]
    s_array = [scale[0], scale[1], scale[2]]
    return t_array, r_array, s_array


def create_camera_description(camera, frame_start=0, frame_end=0,
                              handle_start=None, handle_end=None, add_to_scene_layout=None):
    """
    Creates a camera description .json file for the latest published camera.
    :param camera:
    :param frame_start:
    :param frame_end:
    :param handle_start:
    :param handle_end:
    :param add_to_scene_layout:
    :return: returns a key/value pair
    """
    from cgl.plugins.blender.tasks.cam import get_latest

    translate, scale, rotate = get_transform_arrays(camera)
    seq, shot = camera.split('_')
    seq = seq.replace('cam', '')
    camera_dict = CONFIG['layout']['asset']
    latest_obj = get_latest(seq, shot)
    add_matching_files(latest_obj.path_root, camera_dict)
    if not handle_start:
        handle_start = frame_start
    if not handle_end:
        handle_end = frame_end

    matrix = get_matrix(camera)
    matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
    camera_dict['name'] = camera
    camera_dict['source_path'] = latest_obj.path
    camera_dict['task'] = latest_obj.task
    camera_dict['transform'] = matrix
    camera_dict['type'] = 'camera'
    camera_dict['frame_start'] = frame_start
    camera_dict['frame_end'] = frame_end
    camera_dict['handle_start'] = handle_start
    camera_dict['handle_end'] = handle_end
    camera_dict['published_from'] = scene_object().path
    camera_dict['translate'] = [translate[0], translate[1], translate[2]]
    camera_dict['rotate'] = [rotate[0], rotate[1], rotate[2]]
    camera_dict['scale'] = [scale[0], scale[1], scale[2]]
    if add_to_scene_layout:
        add_item_to_scene_description(camera, camera_dict)
    return camera, camera_dict


def get_matrix(obj=None, query=False):
    """
    Returns a matrix of values relating to translate, scale, rotate.
    :param obj:
    :param query:
    :return:
    """
    if not query:

        if objExists(obj.name):
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
                attr = "%s.%s".format(obj, 'matrix')

                matrix = [[obj.matrix_world.to_translation().x,
                           obj.matrix_world.to_translation().y,
                           obj.matrix_world.to_translation().z],
                          [obj.matrix_world.to_euler().x,
                           obj.matrix_world.to_euler().y,
                           obj.matrix_world.to_euler().z],
                          [obj.matrix_world.to_scale().x,
                           obj.matrix_world.to_scale().y,
                           obj.matrix_world.to_scale().z]]
        #                else:
        #                    matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        else:
            matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        return matrix
    else:
        return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def set_matrix(obj, matrix=None):
    """
    Sets translate, rotate, scale values according to matrix value given
    :param obj:
    :param matrix:
    :return:
    """
    r_matrix = []
    if not matrix:
        matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    for manip in matrix:
        for val in manip:
            r_matrix.append(val)
    if pm.objExists(obj):
        pm.xform(obj, m=r_matrix)


def compare_matrix(matrix_a, matrix_b):
    for num, t in enumerate(matrix_a):
        a = float(matrix_b[num])
        if round(t, 3) != round(a, 3):
            return False
    return True


def publish_layout():
    """
    exports a layout of the current scene
    :return:
    """
    lobj = scene_object().copy(task='lay', latest=True, set_proper_filename=True, ext='json', user='publish',
                               context='render')
    lobj = lobj.next_major_version()
    os.makedirs(os.path.dirname(lobj.path_root))
    return create_scene_description(lobj.path_root)


def export_bndl():
    """
    exports a bundle of the current scene, this is designed for the actual 'bndl' task.
    a bundle can contain assets as children.  A layout can contain bundles as children.
    :return:
    """
    # TODO - i should make sure the tag on the object is updated when i do this.
    if scene_object().task == 'bndl':
        lobj = scene_object().copy(task='bndl', set_proper_filename=True, ext='json',
                                   context='render')
        return create_scene_description(lobj.path_root)
    else:
        print('attempting to export_bndl from a non-bundle scene')


def create_scene_description(sd_path, ignore_bundles=True):
    """
    Creates the scene description file.   This can be used for a layout or a bundle
    :param sd_path:
    :param ignore_bundles:
    :return:
    """

    assign_bundlePath()
    json_render_path = sd_path
    excluded_bundle_refs = []
    if json_render_path:
        layout_dict = {}
        if ignore_bundles:
            excluded_bundle_refs = get_bundle_ref_children()
        references = get_bundles()

        for obj in references:

            filepath_library = get_lib_from_object(obj)
            if filepath_library not in excluded_bundle_refs:
                if obj.users >= 1:
                    asset, description = create_asset_description(obj)
                    if asset:
                        layout_dict[asset] = copy.copy(description)
                else:
                    print('adding bundle to layout')
        # print(layout_dict)
        print(json_render_path.replace('msd', 'json'))
        import pprint
        pprint.pprint(layout_dict)
        save_json(json_render_path, layout_dict)
        print('Saved scene description to: {}'.format(json_render_path))
        return json_render_path
    else:
        return False


def add_item_to_scene_description(item_name, item_dict, layout_json_path=None):
    """
    adds the given item and item_dict to a scene description (layout.json file.)
    tpyically item_name and item dict will come from create_asset_description, or create_camera_description.
    :param item_name:
    :param item_dict:
    :param layout_json_path: this refers to the layout scene description we'd be adding the item to.
    :return:
    """
    import cgl.plugins.maya.tasks.lay as task_lay
    reload(task_lay)
    if not layout_json_path:
        layout_json_path = task_lay.get_latest().path_root
    print('loading layout: {}'.format(layout_json_path))
    layout_asd = load_json(layout_json_path)
    layout_asd[item_name] = copy.copy(item_dict)
    print('added {} to {}'.format(item_name, layout_json_path))
    save_json(layout_json_path, layout_asd)


def get_bundles():
    """
    retrieves all "bundles" in a scene
    :return: list of bundles
    """

    bundles = []

    sel = bpy.data.objects

    for obj in sel:
        if 'BundlePath' in obj.keys():
            bundles.append(obj)
    return bundles


def get_bundle_ref_children():
    """
    Returns a list of all the children of bundles.  This is used when avoiding adding bundle children to a layout
    scene description.
    :return:
    """
    bundle_ref_children = []
    bundles = get_bundles()
    for b in bundles:
        children = b.children
        for child in children:
            try:
                ref = get_lib_from_object(child)
                bundle_ref_children.append(ref)
            except RuntimeError:
                logging.info('%s is not a reference' % child)
    return bundle_ref_children


def assign_bundlePath():
    for obj in bpy.data.objects:
        if obj.type == 'EMPTY':
            if obj.is_instancer:
                lib = get_lib_from_object(obj)
                if lib:
                    obj['BundlePath'] = return_lib_path(lib)
                else:
                    obj['BundlePath'] = 'NOT BUNDLED'


def return_asset_name(obj):
    if 'proxy' in obj.name:
        name = obj.name.split('_')[0]
        return name

    else:
        if '.' in obj.name:

            name = obj.name.split('.')[0]
        else:
            name = obj.name

        return name


def get_lib_from_object(object):
    if not object.is_instancer:
        object = bpy.data.object[return_asset_name(object)]
    library = object.instance_collection.library

    return (library)


def return_lib_path(library):
    from pathlib import Path

    print(library)
    library_path = library.filepath
    # filename = Path(bpy.path.abspath(library_path)).__str__()
    return (library_path)

def add_source_path(obj, path_object):
    from cgl.plugins.blender.utils import get_objects_in_hirarchy, get_object

    tag_list = get_objects_in_hirarchy(obj)

    for each in tag_list:
        object = get_object(each)
        object['source_path'] = path_object.path


if __name__ == '__main__':
    assign_bundlePath()

    scene = scene_object().copy(ext='msd')
    create_scene_description(scene.path_root)