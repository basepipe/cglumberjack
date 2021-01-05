from cgl.plugins.blender.tasks.smart_task import SmartTask
from cgl.plugins.blender import utils
from cgl.plugins.blender import lumbermill as lm
import bpy

class Task(SmartTask):

    def __init__(self, path_object=None):

        if not path_object:
            from cgl.plugins.blender.lumbermill import scene_object
            self.path_object = scene_object().copy(task = 'mdl', set_proper_filename=True,latest=True)
        else:
            self.path_object = path_object
    def build(self):
        from cgl.plugins.blender.alchemy import selection
        from cgl.plugins.blender.utils import create_shot_mask_info
        task = 'mdl'
        selection(clear=True)

        objects = bpy.data.objects

        if task in objects:
            print('MDL already exists')
            pass
        else:
            print('please_create_material_groups')

        create_material_groups()

        #bpy.ops.object.fix_collection_name()
        bpy.ops.object.correct_file_name()
        utils.create_shot_mask_info()
        defaultShotSettings()

class CreateMaterialsGroups(bpy.types.Operator):
    import bpy
    bl_idname = "object.create_material_groups"
    bl_label = "create material groups"

    high = bpy.props.BoolProperty(
        name="high",
        description="high",
        default=True
    )

    mdl = bpy.props.BoolProperty(
        name="mdl",
        description="mdl",
        default=True
    )

    def execute(self, context):

        if bpy.types.Scene.inputDialogSelectionRegex[1]['default']:

            cleaned_list = []
            full_list = ['mdl','high']
            materials = bpy.types.Scene.inputDialogText.split(',')

            print(materials)

            for each in materials:
                each = each.replace(' ', '')
                each = '%s_mtl' % each
                cleaned_list.append(each)

            re = bpy.types.Scene.inputDialogSelectionRegex[1]['default']
            selection = bpy.types.Scene.inputDialogSelection[1]['default']

            print(materials)
            root = None
            high = None
            asset = lm.scene_object().asset
            if self.mdl:

                root = utils.create_object('mdl',collection=asset)
                res = bpy.data.objects['mdl']
                root.empty_display_size = 1

            if self.high:
                utils.create_object('high', parent=root,collection=asset)
                res = bpy.data.objects['high']
                res.empty_display_size = 0.001

            for element in cleaned_list:
                print(element)
                elem = utils.create_object(element, parent=res,collection=asset)
                elem.empty_display_size = 0.001

            for material in res.children:
                if material.name not in cleaned_list:
                    cleaned_list.append(material.name)
                    print('existing materials')
                    print('material.name')
                    material.empty_display_size = 0.001

            full_list += cleaned_list
            for element in full_list:
                print(asset)
                utils.parent_to_collection(obj = lm.get_object(element),
                                           collection_name= asset)



            lm.confirm_prompt(message='Material Groups created, please move geometries to groups')

            return {'FINISHED'}

        else:
            self.report({'INFO'}, 'no valid Material Names')
            return {'CANCELLED'}

def defaultShotSettings():
    scene = bpy.context.scene
    scene.eevee.taa_render_samples = 1
    scene.eevee.taa_samples = 1
    scene.eevee.shadow_cube_size = '2048'

def create_high_group(materials):

    from cgl.plugins.blender.utils import selection
    selection(clear=True)
    for m in materials:
        print('selecting material')
        # pm.select(m, tgl=True)
    print('create group high')
    # pm.group(name='high')

def create_mdl_group(res='high'):
    utils.create_collection('mdl')

def create_material_groups(do_high=True, do_mdl=True):
    try:
        bpy.utils.register_class(CreateMaterialsGroups)
    except ValueError:
        pass

    dialog = lm.InputDialog(title='Create Material Groups',
                            message='List materials needed in this object (comma seperated)', line_edit=True,
                            regex='^([a-z]{3,}, *)*[a-z]{3,}', name_example='ex: wood, metal',
                            command='bpy.ops.object.create_material_groups()')

def get_mdl_objects(group= 'high', namespace = None):
    """
    returns a list of tuples with the objects and it's material group
    :param group:
    :type group:
    :return:
    :rtype:
    """
    from cgl.plugins.blender import  utils
    from importlib import  reload
    reload(utils)
    mdl_objects = []
    group_name = group

    if namespace:
        group_name = '{}:{}'.format(namespace,group)
    geo_group = utils.get_object(group_name)

    for mtl in geo_group.children:
        for obj in mtl.children:
            mdl_objects.append((obj, mtl.name))

    return mdl_objects

def export_mesh(type = 'abc'):
    """
    exports all the rigs in the scene
    :return:
    :rtype:
    """
    from cgl.plugins.blender.alchemy import export_selected, scene_object, selection


    selection(clear=True)

    for obj in get_mdl_objects():
        selection(object=obj)

    render_path = scene_object().copy(context = 'render', ext = type)

    export_selected(render_path.path_root)
    print(render_path.path_root)
    print(get_rigs_in_scene())