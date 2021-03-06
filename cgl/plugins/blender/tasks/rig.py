from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Read layout for file
        2. Import Camera
        :return:
        """
        from cgl.plugins.blender.utils import create_shot_mask_info , rename_collection
        from cgl.plugins.blender.alchemy import scene_object
        from cgl.plugins.blender.tasks.mdl import remove_mdl_group
        import bpy

        #bpy.ops.object.correct_file_name()


        #model = alc.scene_object().copy(task='mdl', set_proper_filename=True).latest_version()
        print('Building rig ')

        remove_mdl_group()
        alc.import_task(task='mdl')

        #bpy.ops.object.fix_collection_name()
        #assign_rig()



    def _import(self, filepath):
        pass



def get_rig(asset= None):
    import bpy
    from cgl.plugins.blender.utils import get_object
    if asset == None :
        asset = alc.scene_object().asset

    asset_name = '{}_rig'.format(asset)
    object = get_object(asset_name)
    return object

def tag_rig():
    import bpy
    from cgl.plugins.blender.tasks import mdl
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.plugins.blender.msd import tag_object
    mdl_objects = mdl.get_mdl_objects(namespace=scene_object().asset)
    act = bpy.context.active_object
    rig = get_rig()

    for obj in mdl_objects:
        if obj != act:
            if 'baseMesh' not in obj[0].name:
                tag_object(obj[0], 'rig_layer', 'SECONDARY')

            elif 'baseMesh' in obj[0].name:
                tag_object(obj[0], 'rig_layer', 'BASEMESH')


def copy_vertex_weights_from_basemesh():
    from cgl.plugins.blender.tasks import mdl

    from cgl.plugins.blender.tasks import rig
    from cgl.plugins.blender.alchemy import scene_object

    mdl_objects = mdl.get_mdl_objects(namespace=scene_object().asset)
    for obj in mdl_objects:
        if obj[0]['rig_layer'] == 'SECONDARY':
            print(obj[0].name)
            rig.copy_vertex_weight(rig.get_base_mesh(), obj[0])


def add_armature_modifier(default =True ):
    import bpy
    from cgl.plugins.blender.tasks import mdl
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.plugins.blender.msd import tag_object
    mdl_objects = mdl.get_mdl_objects(namespace=scene_object().asset)
    act = bpy.context.active_object
    rig = get_rig()

    for obj in mdl_objects:
        if obj != act:
            bpy.context.view_layer.objects.active = obj[0]

            if 'Armature' not in obj[0].modifiers:
                bpy.ops.object.modifier_add(type='ARMATURE')


            armature_modifier = obj[0].modifiers["Armature"]

            armature_modifier.object = rig


def assign_rig():
    tag_rig()
    copy_vertex_weights_from_basemesh()
    add_armature_modifier()


def get_mdl_mesh(arg = None, all = False):
    from cgl.plugins.blender.utils import get_object
    from ..alchemy import scene_object
    from .mdl import get_mdl_objects
    assetName = scene_object().asset


    object_name = '{}:{}'.format(assetName,arg)

    if all :
        return get_mdl_objects(namespace=assetName)

    else:
        return get_object(object_name)


def get_base_mesh():
    from .mdl import get_mdl_objects
    for obj in get_mdl_objects():
        if  obj[0]['rig_layer'] =='BASEMESH' :
            return obj[0]

def copy_vertex_weight(source,dest):
    import bpy
    try:
        obj = dest
        obj.data.use_auto_smooth = True
        mod = obj.modifiers.new("data_transfer", 'DATA_TRANSFER')
        scn = bpy.context.scene

        mod.object = source
        mod.use_vert_data = True
        mod.data_types_verts = {'VGROUP_WEIGHTS'}

        bpy.ops.object.datalayout_transfer(modifier='data_transfer')
        bpy.ops.object.modifier_apply(modifier="data_transfer")


    except(AttributeError):
        pass


def remove_controllers(obj= None):
    if obj == None:
        obj = bpy.context.object

    vertex_groups = bpy.context.object.vertex_groups

    for group in vertex_groups:
        if 'fs:' in group.name:
            vg = obj.vertex_groups.get(group.name)
            if vg is not None:
                obj.vertex_groups.remove(vg)
                print(group.name)

def remove_unused_weights(ob = None):

    if obj == None:
        obj = bpy.context.active_object
    obj.update_from_editmode()

    vgroup_used = {i: False for i, k in enumerate(obj.vertex_groups)}
    vgroup_names = {i: k.name for i, k in enumerate(obj.vertex_groups)}

    for v in obj.data.vertices:
        for g in v.groups:
            if g.weight > 0.0:
                vgroup_used[g.group] = True
                vgroup_name = vgroup_names[g.group]
                armatch = re.search('((.R|.L)(.(\d){1,}){0,1})(?!.)', vgroup_name)
                if armatch != None:
                    tag = armatch.group()
                    mirror_tag = tag.replace(".R", ".L") if armatch.group(2) == ".R" else tag.replace(".L", ".R")
                    mirror_vgname = vgroup_name.replace(tag, mirror_tag)
                    for i, name in sorted(vgroup_names.items(), reverse=True):
                        if mirror_vgname == name:
                            vgroup_used[i] = True
                            break
    for i, used in sorted(vgroup_used.items(), reverse=True):
        if not used:
            obj.vertex_groups.remove(obj.vertex_groups[i])

def get_msd_info(mesh):
    """
    gets the .msd info for a given mesh
    :param mesh:
    :return:
    """
    from cgl.core.config.config import ProjectConfig
    from os.path import join
    from ..alchemy import set_relative_paths
    from cgl.core.path import PathObject
    from..msd import get_matrix, get_transform_arrays
    set_relative_paths(True)
    rig_dict = {}
    if mesh['layer']:
        rig_dict['layer'] = mesh['layer']

    rel_path = mesh['source_path']
    print(mesh)
    print(rel_path)
    ref_path = join(ProjectConfig().root_folder, rel_path)
    path_object = PathObject(ref_path)
    matrix = get_matrix(mesh,rig_root = mesh['main_controller'])
    matrix = str(matrix).replace('[', '').replace(']', '').replace(',', '')
    translate, rotate, scale = get_transform_arrays(mesh)

    rig_dict['msd_path'] = path_object.relative_msd_path
    rig_dict['transform'] = {'matrix': matrix,
                             'scale': scale,
                             'rotate': rotate,
                             'translate': translate
                             }
    rig_dict['main_controller'] = mesh['main_controller']
    rig_dict['source_path'] = rel_path
    set_relative_paths(False)
    return rig_dict


