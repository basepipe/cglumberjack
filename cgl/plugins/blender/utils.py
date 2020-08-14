import re
import os
import sys
import stringcase
import logging
import cgl.core.utils.read_write as read_write
from cgl.core.path import get_resources_path
from cgl.core.project import get_cgl_tools

import json
logger = logging.getLogger('qtutils')


def get_menu_path(software, menu_name, menu_file=False, menu_type='menus'):
    """
    returns the menu path for a menu with the given name
    :param software: software package to get the menu path for.
    :param menu_name: CamelCase string - all menus created with pipeline designer are CamelCase
    :param menu_file: if True returns a menu path with a menu_name.py file.
    :param menu_type: menus, preflights, shelves, context-menus
    :return:
    """
    if menu_file:
        if isinstance(menu_name, dict):
            menu_name = menu_name['name']
        menu_folder = os.path.join(get_cgl_tools(), software, menu_type, menu_name, '%s.py' % menu_name)
    else:
        menu_folder = os.path.join(get_cgl_tools(), software, menu_type, menu_name)
    return menu_folder


def get_button_path(software, menu_name, button_name, menu_type='menus'):
    """

    :param software: software as it appears in pipeline designer.
    :param menu_name: CamelCase menu name
    :param button_name: CamelCase button name
    :param menu_type: menus, preflights, shelves, context-menus
    :return:
    """
    menu_folder = get_menu_path(software, menu_name, menu_type=menu_type)
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


def create_menu_file(class_name):
    """
    Creates a Menu File on Disk
    :param class_name: name for the class
    :param label: the label for the menu
    :param menu_path: path to the resulting menu.py file.
    :return:
    """
    # read in the menu file
    menu_path = get_menu_path('blender', class_name, menu_file=True)
    menu_template = os.path.join(get_resources_path(), 'pipeline_designer',
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


def create_button_file(class_name, label, menu_name):
    """
    Creates a Blender Button File on Disk.
    :param class_name: name of the class
    :param label: label to appear on the button
    :param menu_name: name of the parent menu (CamelCase)
    :return:
    """
    button_path = get_button_path('blender', menu_name, class_name)
    button_template = os.path.join(get_resources_path(), 'pipeline_designer',
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


def add_buttons_to_menu(menu_name):
    """
    adds buttons from a cgl menu config file to a blender menu
    :param menu_class:
    :param button_list:
    :return:
    """
    menu_file = get_menu_path('blender', menu_name, '%s.py' % menu_name)
    menu_config = os.path.join(get_cgl_tools(), 'blender', 'menus.cgl')
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


def write_layout(outFile = None):
    from cgl.plugins.blender.lumbermill import scene_object, LumberObject, import_file
    import bpy
    from pathlib import Path
    import json
    if outFile == None:
        outFile = scene_object().copy(ext='json', task='lay', user='publish').path_root
    data = {}

    for obj in bpy.data.objects:
        if obj.is_instancer:
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
            libraryPath = bpy.path.abspath(obj.instance_collection.library.filepath)
            filename = Path(bpy.path.abspath(libraryPath)).__str__()
            libObject = LumberObject(filename)

            data[name] = {'name': libObject.asset,
                          'source_path': libObject.path,
                          'blender_transform': blender_transform}

    with open(outFile, "w") as library_data_file:
        json.dump(data, library_data_file, indent=4, sort_keys=True)

    return (outFile)


def read_layout(outFile = None ):
    from cgl.plugins.blender.lumbermill import scene_object, LumberObject, import_file
    import bpy

    if outFile == None:

        outFileObject = scene_object().copy(ext='json', task='lay', user='publish').latest_version()
        outFileObject.set_attr(filename='%s_%s_%s.%s' % (outFileObject.seq,
                                                       outFileObject.shot,
                                                       outFileObject.task,
                                                       'json'
                                                       ))
        outFile= outFileObject.path_root
    #outFile = scene_object().path_root.replace(scene_object().ext, 'json')

    with open(outFile) as json_file:
        data = json.load(json_file)
        for p in data:
            print(p)
            data_path = data[p]['source_path']
            blender_transform = data[p]['blender_transform']

            transform_data = []
            for value in blender_transform:
                transform_data.append(value)

            print(transform_data)

            pathToFile = os.path.join(scene_object().root, data_path)
            lumberObject = LumberObject(pathToFile)

            if lumberObject.filename not in bpy.data.libraries:
                import_file(lumberObject.path_root, linked=False)
            if p not in bpy.data.objects:
                obj = bpy.data.objects.new(p, None)
                bpy.context.collection.objects.link(obj)
                obj.instance_type = 'COLLECTION'
                obj.instance_collection = bpy.data.collections[lumberObject.asset]
                obj.location = (transform_data[0], transform_data[1], transform_data[2])
                obj.rotation_euler = (transform_data[3], transform_data[4], transform_data[5])
                obj.scale = (transform_data[6],transform_data[7],transform_data[8])

    bpy.ops.file.make_paths_relative()


def rename_materials(selection = None):
    import bpy
    """
    Sequentially renames  materials from given object name if empty , renamed from selected object
    :param name:
    """
    if selection == None:
        selection = bpy.context.selected_objects


        for object in selection:
            for material_slot in object.material_slots:
                material_slot.material.name = object.name
                print(object.name, material_slot.name)

    if selection:
        selection = [bpy.data.objects[selection]]
        for object in selection:
            for material_slot in object.material_slots:
                material_slot.material.name = object.name
                print(object.name, material_slot.name)


def setup_preview_viewport_display(color=None, selection=None):
    import bpy
    """
    set up the default viewport display color  diffuse_color on materials
    :param color: Value of the color  of the parent menu  FloatProperty 4
    :param selection:
    """
    if selection == None:
        selection = bpy.context.selected_objects

    for object in selection:
        for material_slot in object.material_slots:
            material = material_slot.material
            node_tree = material.node_tree.nodes
            if color == None:
                for node in node_tree:
                    if node.type == 'OUTPUT_MATERIAL':
                        for input in node.inputs:
                            if len(input.links) != 0:
                                input_surface = input.links[0].from_node
                                color_input = input_surface.inputs[0]
                                try:
                                    color_input_nested = color_input.links[0].from_node
                                    color_input.default_value = color_input_nested.outputs[0].default_value
                                except(IndexError):
                                    print('no color inputs found. Using Default')
                                    pass

                                material.diffuse_color = color_input.default_value
            else:
                material_slot.material.diffuse_color = color


if __name__ == '__main__':
    # create_menu_file('TomTest', 'Tom Test', r'F:\FSU-CMPA\COMPANIES\_config\cgl_tools\blender\menus\TomTest\TomTest.py')
    # create_button_file('ButtonAaa', 'Button Aaa', 'TomTest')
    add_buttons_to_menu('TomTest')


