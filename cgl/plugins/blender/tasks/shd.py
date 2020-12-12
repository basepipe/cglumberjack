from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.blender.utils import load_plugin, get_object_list
from cgl.plugins.blender import lumbermill as lm
import bpy


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        model_ref = lm.import_task(task='mdl', reference=True)
        lm.import_task(task='tex', ref_node=model_ref)



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

        lm.selection(clear=True)



def read_materials(path_object=None):
    """

    :type path_object: object
    """
    from cgl.plugins.blender import lumbermill as lm
    from cgl.core.utils.read_write import load_json
    """
    Reads the materials on the shdr task from defined from a json file
    :return:
    """
    import bpy
    if path_object == None:
        path_object = lm.scene_object()

    shaders = path_object.copy(task='shd', user='publish', set_proper_filename=True).latest_version()
    outFile = shaders.copy(ext='json').path_root

    data = load_json(outFile)

    for obj in data.keys():
        object = bpy.data.objects[obj]
        # data = object.data
        index = 0

        for material in data[obj].keys():

            if material not in bpy.data.materials:
                lm.import_file_old(shaders.path_root, collection_name=material, type='MATERIAL', linked=False)

            if material not in object.data.materials:
                object.data.materials.append(bpy.data.materials[material])

            face_list = data[obj][material]

            for face in face_list:
                object.data.polygons[face].select = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
            object.active_material_index = index
            bpy.ops.object.material_slot_assign()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            index += 1
