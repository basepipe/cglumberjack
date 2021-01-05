from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.blender.utils import load_plugin
from cgl.plugins.blender import alchemy as alc
import bpy


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
        model_ref = alc.import_task(task='mdl', reference=True)
        alc.import_task(task='tex', ref_node=model_ref)

    def _import(self, file_path, reference=False,**kwargs):
        from cgl.plugins.blender.alchemy import PathObject
        print(444444444)
        self.path_object = PathObject(file_path)
        print(file_path)
        read_materials(filepath=file_path)

    def import_latest(self,task=None, reference=False, file_path= None,**kwargs):
        from cgl.plugins.blender.alchemy import PathObject
        if not task:
            task = self.path_object.task
        new_obj = PathObject(file_path)

        import_obj = self._import(new_obj.path_root, reference=reference)
        return import_obj



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

def write_materials_msd(ref_object = None):
    from cgl.plugins.blender.utils import create_task_on_asset
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.core.utils.read_write import save_json


    path_object = create_task_on_asset('shd', path_object = ref_object)

    outFile = path_object.copy(ext='msd',context = 'render').path_root


    save_json(outFile, data= get_materials_dictionary())

def check_material_count(max_count = 1 ):

    dic = get_materials_dictionary()
    material_count = []
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
        print(item)

        materials = dic[item].keys()

        if len(materials) > 1:
            print(item)
            bpy.data.objects[item].select_set(True)
            bpy.ops.mesh.separate(type='MATERIAL')

        alc.selection(clear=True)

def import_materials(filepath):

    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        # data_to.cameras = [c for c in data_from.cameras if c.startswith(collection_name)]
        data_to.materials = [c for c in data_from.materials]


    print('{} material imported '.format(filepath))


def assign_material_groups(elements = None):
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




def read_materials(filepath=None, mdl_group= None):
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

            assign_material_to_children(mat.name,asset=asset)


    return materials



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
    from cgl.plugins.blender.lumbermill import scene_object
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


def assign_material_to_children(shader,asset):
    import bpy
    from ..utils import get_object,selection
    mtl_name = shader.replace('shd', 'mtl')

    material_name = shader
    SG_path = bpy.data.materials[material_name]

    object = get_object(mtl_name)

    for obj in object.children:
        obj.material_slots[0].material = SG_path
