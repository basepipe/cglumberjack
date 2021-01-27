import logging
import os
from cgl.core.config.config import ProjectConfig
import stringcase
import cgl.core.utils.read_write as read_write

logger = logging.getLogger('qtutils')


def get_menu_path(software, menu_name, menu_file=False, menu_type='menus', cfg = None):

    """
    returns the menu path for a menu with the given name
    :param cfg:
    :type cfg:
    :param software: software package to get the menu path for.
    :param menu_name: CamelCase string - all menus created with cookbook designer are CamelCase
    :param menu_file: if True returns a menu path with a menu_name.py file.
    :param menu_type: menus, pre_publish, shelves, context-menus
    :return:
    """
    if cfg == None:
        cfg = ProjectConfig()
    if menu_file:
        if isinstance(menu_name, dict):
            menu_name = menu_name['name']
        menu_folder = os.path.join(cfg.cookbook_folder, software, menu_type, menu_name, '%s.py' % menu_name)
    else:
        menu_folder = os.path.join(cfg.cookbook_folder, software, menu_type, menu_name)
    return menu_folder

def get_button_path(software, menu_name, button_name, menu_type='menus',cfg = None):
    """

    :param software: software as it appears in cookbook designer.
    :param menu_name: CamelCase menu name
    :param button_name: CamelCase button name
    :param menu_type: menus, pre_publish, shelves, context-menus
    :return:
    """
    if cfg == None:
        cfg = ProjectConfig()

    menu_folder = get_menu_path(software, menu_name, menu_type=menu_type,cfg= cfg)
    button_path = os.path.join(menu_folder, '%s.py' % button_name)
    return button_path

def create_tt(length, tt_object):
    """
    Creates a turntable with frame range of 0-length, around the selected object.
    :param length:
    :param tt_object:
    :return:
    """
    pass

def clean_tt(task=None):
    pass

def get_current_camera():
    pass

def confirm_prompt(title='title', message='message', button='Ok'):
    """
    standard confirm prompt, this is an easy wrapper that allows us to do
    confirm prompts in the native language of the application while keeping conventions
    :param title:
    :param message:
    :param button: single button is created with a string, multiple buttons created with array
    :return:
    """
    pass

def load_plugin(plugin_name):
    pass

def basic_playblast(path_object, appearance='smoothShaded', cam=None, audio=False):
    pass

def create_menu_file(class_name,cfg):
    """
    Creates a Menu File on Disk
    :param class_name: name for the class
    :param label: the label for the menu
    :param menu_path: path to the resulting menu.py file.
    :return:
    """
    # read in the menu file
    menu_path = get_menu_path('blender', class_name, menu_file=True,cfg = cfg)

    menu_template = os.path.join(cfg.get_cgl_resources_path(), 'alchemists_cookbook',
                                 'blender', 'PanelTemplate.py')


    menu_lines = read_write.load_text_file(menu_template)
    changed_lines = []
    for l in menu_lines:
        if l.startswith('class PanelTemplate'):
            new_l = l.replace('class PanelTemplate', 'class %s' % class_name)
            changed_lines.append(new_l)
        elif 'Panel Template' in l:
            new_l = l.replace('Panel Template', stringcase.titlecase(class_name))
            changed_lines.append(new_l)
        else:
            changed_lines.append(l)
    read_write.save_text_lines(changed_lines, menu_path)
    # change class_name and lables
    # write out the menu file to desired location
    pass

def create_button_file(class_name, label, menu_name,cfg):
    """
    Creates a Blender Button File on Disk.
    :param class_name: name of the class
    :param label: label to appear on the button
    :param menu_name: name of the parent menu (CamelCase)
    :return:
    """
    button_path = get_button_path('blender', menu_name, class_name,cfg)
    button_template = os.path.join(cfg.get_cgl_resources_path(), 'alchemists_cookbook',
                                   'blender', 'buttonTemplate.py')
    button_lines = read_write.load_text_file(button_template)
    changed_lines = []
    for l in button_lines:
        if l.startswith('class ButtonTemplate'):
            new_l = l.replace('ButtonTemplate', class_name)
            changed_lines.append(new_l)
        elif 'object.button_template' in l:
            new_l = l.replace('button_template', stringcase.snakecase(class_name))
            changed_lines.append(new_l)
        elif 'bl_label' in l:
            new_l = l.replace('button_template', label)
            changed_lines.append(new_l)
        elif 'print' in l:
            new_l = l.replace('button_template', label)
            changed_lines.append(new_l)
        else:
            changed_lines.append(l)
    read_write.save_text_lines(changed_lines, button_path)
    # Add a row to the Menu File

def add_buttons_to_menu(menu_name, cfg = None):
    """
    adds buttons from a cgl menu config file to a blender menu
    :param menu_class:
    :param button_list:
    :return:
    """
    menu_file = get_menu_path('blender', menu_name, '%s.py' % menu_name,cfg=cfg)
    menu_config = os.path.join(ProjectConfig().cookbook_folder, 'blender', 'menus.cgl')
    menu_object = read_write.load_json(menu_config)
    biggest = get_last_button_number(menu_object, 'blender', menu_name)
    if biggest:
        menu_lines = read_write.load_text_file(menu_file)
        new_menu_lines = []
        for ml in menu_lines:
            if 'pass' in ml:
                if remove_pass:
                    continue
            new_menu_lines.append(ml)
            if 'ADD BUTTONS' in ml:
                break
        i = 0
        while i < biggest:
            button_name = get_menu_at(menu_object, 'blender', menu_name, i)
            print('\t\t', button_name)
            button_string = '        self.layout.row().operator("object.%s")\n' % stringcase.snakecase(button_name)
            new_menu_lines.append(button_string)
            i += 1

        read_write.save_text_lines(new_menu_lines, menu_file)

def get_last_button_number(menu_dict, software, menu):
    for m in menu_dict[software]:
        if m['name'] == menu:
            return len(m['buttons'])

def get_menu_at(menu_dict, software, menu, i):
    for men in menu_dict[software]:
        if men['name'] == menu:
            print(i, len(men['buttons']))
            button_at = men['buttons'][i]
            return button_at['label']

def write_layout(outFile=None):
    """

    :param outFile:
    :return:
    """
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.core.path import PathObject
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
                    libObject = PathObject(filename)

                    data[name] = {'name': libObject.asset,
                                  'source_path': libObject.path,
                                  'blender_transform': blender_transform}
                else:
                    print('{} has no instanced collection'.format(obj.name))

            else:
                print('{} has no instanced collection'.format(obj.name))

    save_json(outFile, data)

    return (outFile)

def return_linked_library(collection):
    import bpy
    '''
    retrieves the linked libraries manually
    '''

    libraries = bpy.data.libraries
    collection_name = collection.split('.')[0]

    for i in libraries:
        if collection in i.name:
            return (i)

def read_layout(outFile=None, linked=False, append=False):
    """
    Reads layout from json file
    :param outFile: path to json file
    :param linked:
    :param append:
    :return:
    """
    from cgl.plugins.blender.alchemy import scene_object, import_file_old
    from cgl.core.path import PathObject
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
        pathObject = PathObject(pathToFile)

        if pathObject.filename_base in bpy.data.libraries:
            lib = bpy.data.libraries[pathObject.filename]
            bpy.data.batch_remove(ids=([lib]))
            import_file_old(pathObject.path_root, linked=linked, append=append)
        else:
            import_file_old(pathObject.path_root, linked=linked, append=append)

        if p not in bpy.data.objects:
            obj = bpy.data.objects.new(p, None)
            bpy.context.collection.objects.link(obj)
            obj.instance_type = 'COLLECTION'
            obj.instance_collection = bpy.data.collections[pathObject.asset]

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

def rename_materials(selection=None, material_name=None):
    """

    Sequentially renames  materials from given object name if empty , renamed from selected object
    :param selection: name of the selection object
    :type selection:
    :param material_name:
    :type material_name:
    """
    import bpy

    if selection == None:
        selection = bpy.context.selected_objects

    if material_name == None:
        if selection.parent:
            material_name = selection.parent.name
        else:
            material_name = selection.name

    for object in selection:
        for material_slot in object.material_slots:
            material_slot.material.name = object.name
            print(object.name, material_slot.name)

    if selection:
        selection = [bpy.data.objects[selection]]
        for object in selection:
            for material_slot in object.material_slots:
                material_slot.material.name = material_name
                print(object.name, material_slot.name)

    cleanup_scene_data(bpy.data.materials)

def get_valid_meshes_list(objects):
    valid_objects = []

    for object in objects:
        if object and object.type == "MESH":
            if object.is_instancer == False:
                valid_objects.append(object)
    return valid_objects

def get_materials_from_object(object):
    valid_materials = []

    for material_slot in object.material_slots:
        material = material_slot.material
        valid_materials.append(material_slot.material)

    return (valid_materials)

def get_selection(selection=None):
    from .alchemy import scene_object
    import bpy
    if selection == None:
        try:
            selection = bpy.context.selected_objects
        except:
            currentScene = scene_object()
            assetName = scene_object().shot
            obj_in_collection = bpy.data.collections[assetName].all_objects

    if not selection:
        selection = bpy.data.objects

    return selection

def get_preview_from_texture(inputs, node_tree):
    texture = None
    if inputs:
        color_input = inputs[1]
        transparent = inputs[2]

        try:
            texture = color_input.links[0].from_node
        except IndexError:
            print('no texture connected')
            pass

    if texture:

        if texture.type == 'TEX_IMAGE':
            preview_color = texture.image.pixels
            diffuse_color = [preview_color[7004],
                             preview_color[7005],
                             preview_color[7006],
                             1 - transparent.default_value]

        if texture.type == "RGB":
            simple_color = texture.outputs['Color'].default_value
            preview_color = [simple_color[1],
                             simple_color[2],
                             simple_color[3],
                             1 - transparent.default_value]

        else:
            preview_color = [1, 1, 1, 1]
            print('_______COMPLEX NODES PLEASE SET MANUALLY_______')
    else:

        inputs = preview_inputs_from_node_tree(node_tree)
        if inputs:

            preview_color = [color_input.default_value[0],
                             color_input.default_value[1],
                             color_input.default_value[2],
                             1]

        else:
            preview_color = [1, 1, 1, 1]

    return preview_color

def preview_inputs_from_node_tree(node_tree):
    color_input = None
    transparent = None
    valid_node = None
    if 'DEFAULTSHADER' in node_tree:
        color_input = node_tree['DEFAULTSHADER'].inputs['Color']
        transparent = node_tree['DEFAULTSHADER'].inputs['Transparent']
        valid_node = node_tree['DEFAULTSHADER']
        found = True
    else:
        found = False
        for node in node_tree:

            if node.type == 'BSDF_PRINCIPLED' and not found:
                color_input = node.inputs[0]
                transparent = node.inputs['Transmission']
                found = True
                valid_node = node

    returns = (valid_node, color_input, transparent)

    if found:
        print('__________Valid Materials And inputs______________')
        print(returns)
        return returns
    else:
        returns = (1, 1, 1, 1)

def setup_preview_viewport_display(object):
    """
    set up the default viewport display color  diffuse_color on materials
    :param color: Value of the color  of the parent menu  FloatProperty 4
    :param selection:
    """
    materials = get_materials_from_object(object)

    for material in materials:
        node_tree = material.node_tree.nodes
        inputs = preview_inputs_from_node_tree(node_tree)
        preview_colors = get_preview_from_texture(inputs, node_tree)

        for i in range(0, 3):
            material.diffuse_color[i] = preview_colors[i]

def get_materials_dictionary():
    """
    creates a dictionary of the objects and the faces associated with that object
    :return: list of materials
    """
    import bpy

    materials = {}

    for o in bpy.context.selected_objects:
        bpy.ops.object.material_slot_remove_unused()
        # Initialize dictionary of all materials applied to object with empty lists
        # which will contain indices of faces on which these materials are applied
        materialPolys = {ms.material.name: [] for ms in o.material_slots}

        for i, p in enumerate(o.data.polygons):
            materialPolys[o.material_slots[p.material_index].name].append(i)
        materials.update({o.name: materialPolys})
    return (materials)

def read_materials(path_object=None):
    """

    :type path_object: object
    """
    from cgl.plugins.blender import alchemy as alc
    from cgl.core.utils.read_write import load_json
    """
    Reads the materials on the shdr task from defined from a json file
    :return:
    """
    import bpy
    if path_object == None:
        path_object = alc.scene_object()

    shaders = path_object.copy(task='shd', user='publish', set_proper_filename=True).latest_version()
    outFile = shaders.copy(ext='json').path_root

    data = load_json(outFile)

    for obj in data.keys():
        object = bpy.data.objects[obj]
        # data = object.data
        index = 0

        for material in data[obj].keys():

            if material not in bpy.data.materials:
                alc.import_file_old(shaders.path_root, collection_name=material, type='MATERIAL', linked=False)

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

def create_task_on_asset(task, path_object=None,version_up = False):
    """
    Creates a task on disk based on path object
    :param task:
    :param path_object:
    :param type: type of task, mdl, shdr,rig etc

    """

    from cgl.plugins.blender import alchemy as alc
    if path_object == None:
        path_object = alc.scene_object()

    newTask = path_object.copy(task=task)
    if version_up:
        newTask =newTask.new_minor_version_object()

    taskFolder = newTask.copy(filename='').path_root


    print('{} creating version'.format(taskFolder))

    print(newTask.path_root)

    sourceFolder = newTask.copy(filename='',context = 'source').path_root
    renderFolder = newTask.copy(filename='',context = 'render').path_root

    folders = [sourceFolder,renderFolder]

    for f in folders:
        if not os.path.isdir(f):
            os.makedirs(f)


    return newTask

def reorder_list(items, arg=''):
    """
    Reorders list in order of importance, putting rig
    :param items:
    :return:
    """

    if arg:

        for i in items:
            if i == arg:
                items.remove(i)
                items.insert(0, arg)

    return items

def get_formatted_list(element, first_item):
    """
    Formats list for blender search mode
    """
    scene = bpy.types.Scene.scene_enum

    path_object = PathObject(get_asset_from_name(scene))
    tasks = reorder_list(path_object.glob_project_element(element), arg=first_item)
    value = [(tasks[i], tasks[i], '') for i in range(len(tasks))]

    return (value)

def unlink_asset(object):
    filepath = None

    try:
        libname = object.data.library
    except AttributeError:
        for lib in bpy.data.libraries:
            libname = object.instance_collection

    print('_________unlinking__________')
    print(object)

    if 'proxy' in object.name:
        name = object.name.split('_')[0]
    else:
        name = object.name

    obj = bpy.data.objects[name]

    if not libname:
        bpy.data.batch_remove(ids=([obj]))
    else:
        try:
            filepath = libname.library.filepath

        except AttributeError:
            pass
        if filepath and PathObject(filepath).type == 'env':
            remove_linked_environment_dependencies(libname.library)

        bpy.data.batch_remove(ids=(libname, obj))
        remove_unused_libraries()

def remove_linked_environment_dependencies(library):
    env = library
    bpy.ops.file.make_paths_absolute()
    env_path = PathObject(env.filepath)
    env_layout = env_path.copy(ext='json').path_root
    env_asset_collection = bpy.data.collections['{}_assets'.format(env_path.asset)]
    data = load_json(env_layout)

    for i in data:
        print(i)
        name = data[i]['name']

        if i in bpy.data.objects:
            obj = bpy.data.objects[i]
            unlink_asset(obj)
    try:

        bpy.data.collections.remove(env_asset_collection)
    except KeyError:
        pass

def remove_unused_libraries():
    libraries = bpy.data.libraries

    objects = bpy.data.objects
    instancers = []

    libraries_in_scene = []

    for obj in objects:
        if obj.is_instancer:
            instancers.append(obj)

    try:
        for i in instancers:
            lib = i.instance_collection.library
            if lib not in libraries_in_scene:
                libraries_in_scene.append(lib)

        for lib in libraries:
            if lib not in libraries_in_scene:
                print(lib)
                # bpy.data.libraries.remove(lib)
                bpy.data.batch_remove(ids=(lib,))
    except AttributeError:
        pass

def remove_instancers():
    for object in bpy.data.objects:

        filepath = None

        try:
            libname = object.data.library
        except AttributeError:
            for lib in bpy.data.libraries:
                libname = object.instance_collection

        print('_________unlinking__________')
        print(object)

        if 'proxy' in object.name:
            name = object.name.split('_')[0]
        else:
            name = object.name

        obj = bpy.data.objects[name]

        if not libname:
            bpy.data.batch_remove(ids=([obj]))
        else:
            try:
                filepath = libname.library.filepath

            except AttributeError:
                pass
            remove_unused_libraries()

def reparent_linked_environemnt_assets(library):
    env = library
    bpy.ops.file.make_paths_absolute()
    env_path = PathObject(env.filepath)
    env_layout = env_path.copy(ext='json').path_root

    data = load_json(env_layout)
    assets_collection_name = '{}_assets'.format(env_path.asset)
    if assets_collection_name not in bpy.data.collections['env'].children:

        assets_collection = bpy.data.collections.new(assets_collection_name)
        bpy.data.collections['env'].children.link(assets_collection)
    else:
        assets_collection = bpy.data.collections[assets_collection_name]

    for i in data:
        print(i)
        name = data[i]['name']

        if i in bpy.data.objects:
            obj = bpy.data.objects[i]
            if assets_collection not in obj.users_collection:
                assets_collection.objects.link(obj)

            keep_single_user_collection(obj, assetName=assets_collection_name)

def keep_single_user_collection(obj, assetName=None):
    if not assetName:
        assetName = alc.scene_object().shot

    try:
        bpy.data.collections[assetName].objects.link(obj)

    except(RuntimeError):
        pass

    for collection in obj.users_collection:
        if collection.name != assetName:
            collection.objects.unlink(obj)

def reparent_collections(view_layer):
    for obj in view_layer:

        if obj.instance_type == 'COLLECTION':
            if obj.instance_collection:

                collection = obj.instance_collection

                print(collection)
                print(collection.library)
                if collection.library:

                    path_object = PathObject(collection.library.filepath)

                    create_collection(path_object.type)
                    for collection in bpy.data.collections:

                        if collection.name == path_object.type:
                            # print(collection.name )

                            if collection not in obj.users_collection:
                                collection.objects.link(obj)

                    keep_single_collections(obj, path_object.type)

    for collection in bpy.context.scene.collection.children:
        if len(collection.objects) < 1:
            print(collection.name)
            bpy.context.scene.collection.children.unlink(collection)

def keep_single_collections(obj, collection_name):
    """
    unlink object from all collections except the one specified

    :param collection_name: name of the collection to keep
    :type collection_name: string
    :param obj: object to adjust
    :type obj: blender object

    """
    user_collections = obj.users_collection
    if len(obj.users_collection) > 1:
        for collection in user_collections:
            if collection.name != collection_name:
                try:
                    print('unlinking {}   {}'.format(obj.name, collection_name))
                    collection.objects.unlink(obj)
                except:
                    pass

def create_collection(collection_name, parent=None):
    import bpy
    """
    creates a colleciton in current scene
    :type collection_name: string

    """
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)

    collection = bpy.data.collections[collection_name]

    if parent == None:
        parent = bpy.context.scene.collection

    else:
        parent = bpy.data.collections[parent]

    try:

        parent.children.link(collection)
    except(RuntimeError):
        print('{} collection already in scene'.format(collection_name))
        pass

    return collection

def parent_to_collection(obj, collection_name,replace = False):
    """

    :param obj: blender object
    :type obj: bpy.data.object
    :param collection_name: str
    :type collection_name: takes in name of the collection
    """
    import bpy
    collection = bpy.data.collections[collection_name]

    if not collection:
        create_collection(collection_name)

    try:
        collection.objects.link(obj)
    except RuntimeError:
        print('{} already in light collection'.format(obj.name))

    if replace:
        for col in obj.users_collection:
            if not col.name == collection_name:
                try:
                    col.objects.unlink(obj)
                    bpy.data.collections.remove(col)
                except:
                    pass

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
    import bpy
    instancer = object.is_instancer
    if not instancer:
        try:
            object = bpy.data.object[return_asset_name(object)]
        except:
            pass
    try:

        library = object.instance_collection.library
    except AttributeError:
        return None
        pass

    return (library)

def return_lib_path(library):
    from pathlib import Path
    print(library)
    library_path = bpy.path.abspath(library.filepath)
    filename = Path(bpy.path.abspath(library_path)).__str__()
    return (filename)

def create_shot_mask_info():
    import bpy
    from .alchemy import scene_object
    current = bpy.context.scene
    mSettings = current.render
    sceneObject = scene_object()
    current.name = sceneObject.filename_base
    scene_info = bpy.context.scene.statistics(bpy.context.view_layer)
    try:
        mSettings.metadata_input = 'SCENE'
    except AttributeError:
        mSettings.use_stamp_strip_meta = 0

    mSettings.stamp_font_size = 26
    mSettings.use_stamp = 1
    mSettings.use_stamp_camera = 1
    mSettings.use_stamp_date = 0
    mSettings.use_stamp_frame = True
    mSettings.use_stamp_frame_range = 0
    mSettings.use_stamp_hostname = 0
    mSettings.use_stamp_labels = 0
    mSettings.use_stamp_lens = 1
    mSettings.use_stamp_marker = 0
    mSettings.use_stamp_memory = 0
    mSettings.use_stamp_note = 0
    mSettings.use_stamp_render_time = 0
    mSettings.use_stamp_scene = 1
    mSettings.use_stamp_sequencer_strip = 0
    mSettings.use_stamp_time = 1
    mSettings.use_stamp_note = True
    mSettings.stamp_note_text = scene_info

    print('shot_mask_created')

def create_object(name, type=None, parent=None,collection = None):
    import bpy
    from cgl.plugins.blender.alchemy import scene_object
    if collection == None:

        collection = bpy.context.collection.name

    if name in bpy.data.objects:
        object = bpy.data.objects[name]
        print('{} object already exists'.format(name))
    else:
        object = bpy.data.objects.new(name, object_data=type )

    if parent:
        object.parent = parent
    parent_to_collection(collection_name=collection,obj=object)

    return object



def parent_object(child, parent, keep_transform=True):
    child.parent = parent
    if keep_transform:
        child.matrix_parent_inverse = parent.matrix_world.inverted()

def clear_parent(objects=None):
    if objects == None:
        objects = bpy.context.selected_objects

    for obj in objects:
        parent = obj.parent
        children = obj.children
        if children:
            for child in children:
                parent_object(child, parent)

def cleanup_scene_data(data_type):
    """
    Deletes data that's not currently linked to any object in scene , takes in bpy.data.type ie
    bpy.data.materials
    :param data_type:
    :type data_type:
    """
    for child in data_type:
        if child.users == 0:
            print(child.name)
            data_type.remove(child)

def return_object_list(task):
    import bpy

    object_list = []

    for res in bpy.data.objects[task].children:
        for materials in res.children:
            for obj in materials.children:
                object_list.append(obj)
    return object_list

def objects_in_scene(string = False):
    import bpy

    list_of_objects = []
    if string == True:
        for object in bpy.data.objects:
            list_of_objects.append(object.name)

        return list_of_objects

    return bpy.data.objects

def get_next_namespace(ns):
    import re
    import bpy
    pattern = '[0-9]+'
    next = False
    sel = bpy.data.objects
    latest = 0

    for i in sel:
        if ns in i.name:
            split_namespace = i.name.split(':')
            if ns == split_namespace[0]:
                num = re.findall(pattern, i.name)
                if num:
                    if int(num[-1]) > latest:

                        latest = int(num[-1])


                next = True

    if next:
        name = '{}'.format(ns)
        return name
    else:
        return ns

def set_framerange(start=1, end=1, current=False):
    import bpy
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end

    current = bpy.context.scene.frame_current
    if current:
        bpy.context.scene.frame_start = current
        bpy.context.scene.frame_end = current

def render(preview=False, audio=False):
    """
    renders the current scene.  Based on the task we can derive what kind of render and specific render settings.
    :param preview: determines if exr is used or not
    :param audio: if True renders an  mov and setups the audio settings
    :return:
    """
    previewRenderTypes = ['anim', 'rig', 'mdl', 'lay']
    file_out = scene_object().render_path.split('#')[0]

    if preview:
        bpy.context.scene.render.image_settings.file_format = 'JPEG'
        bpy.context.scene.render.filepath = file_out

        if audio:
            bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
            bpy.context.scene.render.ffmpeg.format = 'QUICKTIME'
            bpy.context.scene.render.ffmpeg.audio_codec = 'MP3'

        bpy.ops.render.opengl('INVOKE_DEFAULT', animation=True, view_context=True)

    else:
        bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
        bpy.context.scene.render.filepath = file_out
        bpy.ops.render.render(animation=True, use_viewport=True)

def get_framerange():
    import bpy
    start = bpy.context.scene.frame_start
    end  = bpy.context.scene.frame_end

    return(start,end)

def scene_elem(elem):
    import bpy
    return eval('bpy.data.{}'.format(elem))

def get_object(name, namespace = None):

    import bpy
    if isinstance(name,str):


        if namespace:
            name = '{}:{}'.format(namespace,name)

        if name in bpy.data.objects:
            return bpy.data.objects[name]

        else:
            return None

    else:
        return name

def get_layer(name, namespace= None, set_default_namespace = True):
    from .alchemy import scene_object
    scene = scene_object()

    if set_default_namespace == True:

        if namespace == None:
            namespace = '{}_{}'.format(scene.seq, scene.shot)

        layer_name = "{}:{}".format(namespace, name)
    else:
        layer_name = name

    return get_object(layer_name)




def get_collection(name, namespace = None):
    import bpy

    if namespace:
        name = '{}:{}'.format(namespace,name)
    if name in bpy.data.collections:

        return bpy.data.collections[name]
    else:
        return None
def set_framerange(start,end):
    import bpy
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end =  end
    bpy.context.scene.frame_current = start

def selection(object=None, clear=False):
    import bpy
    if clear:

        for ob in bpy.data.objects:
            ob.select_set(False)

    if object:
        object.select_set(True)
        bpy.context.view_layer.objects.active = object

def current_selection(single = False):
    import bpy
    if single:
        return bpy.context.object

    return  bpy.context.selected_objects

def switch_overlays(visible=False):
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_overlays = visible

def read_matrix(obj, transform_data):

    location = (transform_data[0], transform_data[1], transform_data[2])
    obj.location = location

    rotation = (transform_data[3], transform_data[4], transform_data[5])
    obj.rotation_euler = rotation

    scale = (transform_data[6], transform_data[7], transform_data[8])
    obj.scale = scale

def set_collection_name(obj = None):
    from .alchemy import scene_object
    import bpy
    if scene_object().scope == 'assets':
        name = scene_object().asset
    elif scene_object().scope == 'shots':
        name = scene_object().filename_base


    if obj == None:
        if name in bpy.data.collections:
            print('collection exist')
        else:
            if 'Collection' in bpy.data.collections:
                bpy.data.collections['Collection'].name = name

            else:
                print('default Collection not found')
                bpy.context.collection.name = name
 

    else:
        if scene_object().asset in bpy.data.collections:
            print('collection exist ')
        object = bpy.context.object
        object.users_collection[0].name = name


def set_context_view_3d():
    import bpy
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        for area in screen.areas:
            if area.type == 'VIEW_3D':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.screen.screen_full_area(override)

def get_objects_in_hirarchy(obj, levels=10):
    import bpy

    hirarchy = []

    def recurse(obj, parent, depth):
        if depth > levels:
            return
        hirarchy.append(obj.name)
        #print("  " * depth, obj.name)
        for child in obj.children:
            recurse(child, obj, depth + 1)

    recurse(obj, obj.parent, 0)

    return hirarchy

def rename_collection(current_scene=None):
    import bpy
    if current_scene is None:
        current_scene = alc.scene_object()

    if current_scene.scope == 'assets':
        name = current_scene.asset
    else:
        name = current_scene.filename_base

    obj = bpy.context.object

    if obj:
        if current_scene.asset in bpy.data.collections:
            print('collection exist ')
        object = bpy.context.object
        object.users_collection[0].name = name

    else:
        if current_scene.asset in bpy.data.collections:
            print('collection exist')

        else:
            bpy.data.collections['Collection'].name = name


def delete_object(object_to_delete):
    import bpy
    bpy.data.objects.remove(object_to_delete, do_unlink=True)


def get_items(type):
    import bpy
    command = 'bpy.data.{}'.format(type)
    return eval(command)


def move_to_project(project, path_object=None):
    from cgl.core.utils.general import  cgl_copy
    context = ['source', 'render']
    if path_object == None:
        path_object = alc.scene_object()

    for item in context:
        fromDir = path_object.copy(context=item, filename=None).path_root
        toDir = path_object.copy(context=item, filename=None, project=project).path_root
        cgl_copy(fromDir, toDir)



def move_linked_libraries_to_project(project= None):
    import bpy
    from cgl.core.path import PathObject
    bpy.ops.file.make_paths_absolute()
    for lib in bpy.data.libraries:
        path_object = PathObject(lib.filepath)
        print(path_object.path)
        move_to_project(project,path_object)


def update_libraries_project(project=None):
    from cgl.core.path import PathObject
    from cgl.plugins.blender.alchemy import scene_object

    import bpy
    if project == None:
        project = scene_object().project

    bpy.ops.file.make_paths_absolute()
    for lib in bpy.data.libraries:
        path_object = PathObject(lib.filepath)
        new_path = path_object.copy(project=project)
        lib.filepath = new_path.path_root
        print(new_path.path_root)
        lib.reload()


def set_object_names_from_library():
    from cgl.plugins.blender import utils
    from cgl.core.path import PathObject
    import bpy

    from importlib import reload
    reload(utils)

    bpy.ops.file.make_paths_absolute()

    for obj in get_instanced_objects():
        # print(obj[0].name, obj[1].filepath)
        path_object = PathObject(obj[1].filepath)
        next_version_number = utils.get_next_namespace(path_object.asset)
        obj[0].name = '{}:{}'.format(path_object.asset, next_version_number)


if __name__ == '__main__':
    # create_menu_file('TomTest', 'Tom Test',
    # r'F:\FSU-CMPA\COMPANIES\_config\cgl_tools\blender\menus\TomTest\TomTest.py')
    # create_button_file('ButtonAaa', 'Button Aaa', 'TomTest')
    add_buttons_to_menu('TomTest')
