from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.blender.utils import load_plugin
from cgl.plugins.blender import alchemy as alc
import bpy
from ..alchemy import scene_object

DEFAULT_SHADER = 'BSDF_PRINCIPLED'  # TODO - add this in the globals.



class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        from .mdl import remove_mdl_group
        remove_mdl_group()
        model_ref = alc.import_task(task='mdl', reference=False)

        remove_materials()
        alc.import_task(task='tex')
        set_object_materials()

    def _import(self, file_path, reference=False,**kwargs):
        from cgl.plugins.blender.alchemy import PathObject
        self.path_object = PathObject(file_path)
        print(file_path)
        read_materials_msd(filepath=file_path)

    def import_latest(self,task=None, reference=False, file_path= None,**kwargs):
        from cgl.plugins.blender.alchemy import PathObject
        if not task:
            task = self.path_object.task
        new_obj = PathObject(file_path)

        import_obj = self._import(new_obj.path_root, reference=reference)
        return import_obj

def get_materials_in_scene(string = False,default_ns=False):
    import bpy
    materials = []
    if string:
        for mat in bpy.data.materials:
            materials.append(mat.name)
        return materials

    else:
        return bpy.data.materials

def get_materials_dictionary(objects = None):
    """
    creates a dictionary of the objects and the faces associated with that object
    :return: list of materials
    """
    import bpy

    materials = {}
    if not objects:
        objects = get_object_list()


    for o in objects:

        # Initialize dictionary of all materials applied to object with empty lists
        # which will contain indices of faces on which these materials are applied
        materialPolys = {ms.material.name: [] for ms in o.material_slots}

        for i, p in enumerate(o.data.polygons):
            materialPolys[o.material_slots[p.material_index].name].append(i)
        materials.update({o.name: materialPolys})
    return (materials)

def check_material_count(max_count = 1 ):

    dic = get_materials_dictionary()
    assignmaterial_count = []
    for item in dic:
        print(item)

        materials = dic[item].keys()

        if len(materials) > max_count:
            material = '{} {}'.format(len(materials), item)
            material_count.append(material)

    return material_count

def split_materials():

    dic = get_materials_dictionary()

    for item in dic:

        materials = dic[item].keys()
        if len(materials) > 1:
            bpy.data.objects[item].select_set(True)
            bpy.ops.mesh.separate(type='MATERIAL')

        alc.selection(clear=True)

def unlink_material_from_geo(obj=None):
    obj.data.materials.clear()

def assign_material(material,geo = None, clear = False):
    from cgl.plugins.blender.utils import get_selection
    if geo == None:
        geo = get_selection()

    if clear:
        unlink_material_from_geo(geo)

    geo.data.materials.append(material)

def assign_materials_from_shading_group():
    from cgl.plugins.blender.tasks import mdl
    from cgl.plugins.blender.alchemy import scene_object
    import bpy
    objects = mdl.get_mdl_objects()


    for obj in objects:
        geo, material_name = obj
        material_object = get_material(geo.parent.name,create=True)
        assign_material(material_object,geo,clear=True)

def remove_materials(material_list = None ,keep_valid_materials =True):
    valid_material_list = get_valid_material_list()


    if material_list == None:

        scene_materials  = get_materials_in_scene()


    for material in scene_materials:
        if material.name not in valid_material_list:
            print(material)
            scene_materials.remove(material)


    # if keep_valid_materials == False:
    #     for material in scene_materials:
    #         scene_materials.remove(material)

def delete_duplicate_groups(node_name):
    for node in bpy.data.node_groups:
        if node.name.split('.')[0] == node_name:
            if not node.name == node_name:
                bpy.data.node_groups.remove(node)

def fix_material_names(namespace = None):
    from cgl.plugins.blender.tasks import mdl
    from cgl.plugins.blender.alchemy import scene_object

    mdl_group = mdl.get_mdl_objects()


    scene = scene_object()

    for obj in mdl_group:
        geo,material_name =  obj[0],obj[1]

        material_slots = geo.material_slots


        if len(material_slots)>=1 :

            if material_name not in material_slots:
                if get_material(material_name) == None:
                    print(material_name)
                    if not geo.material_slots[0].material == None:

                        geo.material_slots[0].material.name = material_name
                    else:
                        print(geo)
                        unlink_material_from_geo(geo)
    #             material.name = material_name
    #         if not material.name == obj[1]:
    #             obj_material = get_material(obj[1])
    #
    #             if obj[1] in bpy.data.materials:
    #
    #                 obj[0].material_slots[0].material  = bpy.data.materials[obj[1]]
    #             else:
    #                 material.name = obj[1]
    #
    #             for mat in material_slot:
    #                 if not mat.name ==  obj[1]:
    #                     material_slot.data.active_material = mat.material
    #                     bpy.ops.object.material_slot_remove()
    #
    #
    #     else:
    #         error_list.append(obj)
    # valid_material_list = []
    #
    #
    # scene_materials = get_materials_in_scene()




    # for mat in mdl_group:
    #     assign_material_in_hirarchy(mat[1], scene.asset)
    #     valid_material = bpy.data.materials[mat[1]]
    #     valid_material_list.append(valid_material)
    #
    #

def assign_material_groups(elements = None):
    '''
    creates a material group for objects list and it's children
    :param elements:
    :type elements: object list
    :return:
    :rtype:
    '''
    from ..utils import get_objects_in_hirarchy, get_object,selection
    import bpy
    from .anim import get_rigs_in_scene
    if elements == None:
        elements = get_rigs_in_scene(all=True)

    for obj in elements:

        mdl_group = get_objects_in_hirarchy(obj)

        for mdl in mdl_group:
            object = get_object(mdl)
            print(object)
            selection(object, clear=True)
            bpy.ops.object.material_slot_add()

def read_face_list(msd):

    for obj in msd.keys():
        face_list = msd[obj][material]

    for face in face_list:
        object.data.polygons[face].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = [False, False, True]
        object.active_material_index = index
        bpy.ops.object.material_slot_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        index += 1

def get_object_list(materials_dic = None):
    from cgl.plugins.blender.alchemy import scene_object
    import bpy

    if not materials_dic:
        try:
            materials_dic = material_dictionaries()
        except:
            pass
    dic = materials_dic
    obj = bpy.data.objects
    object_list = []
    for task in dic:
        task_null = obj[task]
        print(task_null)
        for res in dic[task]:
            resolution_null = obj[res]
            print(resolution_null)
            for material in dic[task][res]:
                print(material)
                children = bpy.data.objects[material].children

                for obj in children:
                    object_list.append(obj)
    return object_list

def get_material(name, create = False,default_ns = False):
    material = None
    scene_materials = get_materials_in_scene(string=True,default_ns=default_ns)

    if name in scene_materials:
        material = bpy.data.materials[name]

    if material is None and create:
        material = scene_materials.new(name = name)
        material.use_nodes = True

    return material

def get_valid_material_list(mat_group=False,mat_object = False,default_ns = False):
    """

    :return: list of materials names
    :rtype:
    """
    from cgl.plugins.blender.tasks import  mdl
    from importlib import reload

    materials = mdl.get_mdl_objects(groups=True,default_ns=default_ns)

    clean_list = []

    for mat in materials:
       # print(mat.name)
        if mat_group :
            clean_list.append(mat)
        elif mat_object:
            material = get_material(mat.name)
            clean_list.append(material)


        else:
            clean_list.append(mat.name)
    return clean_list

def material_dictionaries(task='mdl'):
    import bpy
    group_task = bpy.data.objects[task]
    resolutions = group_task.children

    material_MSD = {}
    material_MSD[task] = {}
    for res in resolutions:
        material_MSD[task][res.name] = {}
        for mat in res.children:
            objects = []
            for obj in mat.children:
                objects.append(obj.name)
            material_MSD[task][res.name][mat.name] = objects

    return material_MSD

def assign_material_in_hirarchy(shader,asset):
    import bpy
    from ..alchemy import confirm_prompt
    from ..utils import get_object,selection, objects_in_scene
    mtl_name = shader.replace('shd', 'mtl')
    failed_materials  = []
    material_name = shader
    SG_path = bpy.data.materials[material_name]



    if mtl_name not in  objects_in_scene(string=True):
        confirm_prompt(message="didn't find material group, rig is probably not up to date "
                               "please fix rig, and export alembic again")

        return


    object = get_object(mtl_name)
    for obj in object.children:
        obj.material_slots[0].material = SG_path

def write_materials_msd(ref_object = None):
    from cgl.plugins.blender.utils import create_task_on_asset
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.core.utils.read_write import save_json


    path_object = create_task_on_asset('shd', path_object = ref_object)

    outFile = path_object.copy(ext='msd',context = 'render').path_root


    save_json(outFile, data= get_materials_dictionary())

def import_materials(filepath):
    import bpy
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        # data_to.cameras = [c for c in data_from.cameras if c.startswith(collection_name)]
        data_to.materials = [c for c in data_from.materials]


    print('{} material imported '.format(filepath))

def read_materials_msd(filepath=None, mdl_group= None):
    import bpy
    from cgl.plugins.blender import alchemy as alc
    from cgl.core.utils.read_write import load_json
    from .anim import get_animation_mdl_groups
    from ..msd import path_object_from_asset_name
    from ..utils import get_object
    from ..msd import path_object_from_asset_name

    path_object = alc.PathObject(filepath)
    assign_material_groups()
    get_animation_mdl_groups()

    if filepath == None:
         path_object = alc.scene_object()

    shaders = path_object.copy(task='shd',
                               user='publish',
                               set_proper_filename=True,
                               scope = 'assets',
                               context = 'render',
                               latest = True)

    outFile = shaders.copy(ext='msd',context = 'render',latest = True).path_root
    asset = shaders.asset

    data = load_json(outFile)
    materials = []


    import_materials(shaders.path_root)
    for obj in data.keys():

        for material in data[obj].keys():

            print(material)
            materials.append(material)
            try:
                mat = bpy.data.materials[material]
                mat.name = '{}:{}'.format(asset, material)

            except KeyError:
                mat = bpy.data.materials['{}:{}'.format(asset, material)]

            mat.name = '{}:{}'.format(asset,material)

            assign_material_in_hirarchy(mat.name,asset=asset)


    return materials

def set_object_materials():
    fix_material_names()
    assign_materials_from_shading_group()
    remove_materials()

def remove_empty_shd_group():
    print('empty')


def set_preview_color(objects = None):
    D = bpy.data
    if objects == None:
        objects = bpy.context.selected_objects


    for obj in objects:
        if obj.type == 'MESH':

            for slot in obj.material_slots:
                material = slot.material
                try:
                    image_file = material.node_tree.nodes['Image Texture'].image.name  # this refers to an image file loaded into Blender

                    img = D.images[image_file]

                    width = img.size[0]
                    height = img.size[1]
                    if (width != 0) and (height != 0):
                        target = [150, 33]

                        index = (target[1] * width + target[0]) * 4

                        preview_color = [
                            img.pixels[index],  # RED
                            img.pixels[index + 1],  # GREEN
                            img.pixels[index + 2],  # BLUE
                            img.pixels[index + 3]  # ALPHA
                        ]
                except KeyError:
                    if 'MILVIO' in scene_object().project:
                        DEFAULT_SHADER = 'DEFAULTSHADER'

                    default = material.node_tree.nodes[DEFAULT_SHADER]
                    preview_color = [default.inputs[0].default_value[0],
                                     default.inputs[0].default_value[1],
                                     default.inputs[0].default_value[2],
                                     1]


                obj.material_slots[0].material.diffuse_color = (preview_color[0],
                                                                preview_color[1],
                                                                preview_color[2],
                                                                preview_color[3])

                from ..msd import tag_object
                tag_object(obj,'PREVIEW_COLOR',str(preview_color))




