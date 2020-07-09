import re
import os
import sys
import stringcase
import logging
import cgl.core.utils.read_write as read_write
from cgl.core.path import get_resources_path
from cgl.core.project import get_cgl_tools

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


def add_buttons_to_menu(menu):
    """
    adds buttons from a cgl menu config file to a blender menu
    :param menu_class:
    :param button_list:
    :return:
    """
    menu_file = get_menu_path('blender', menu, '%s.py' % menu)
    menu_config = os.path.join(get_cgl_tools(), 'blender', 'menus.cgl')
    menu_object = read_write.load_json(menu_config)
    biggest = get_last_button_number(menu_object, 'blender', menu)
    menu_lines = read_write.load_text_file(menu_file)
    print(menu_object)
    print(menu_lines)
    new_menu_lines = []
    for ml in menu_lines:
        if 'pass' in ml:
            if remove_pass:
                continue
        new_menu_lines.append(ml)
        if 'ADD BUTTONS' in ml:
            i = 0
            while i < biggest:
                i += 1
                button_name = get_menu_at(menu_object, 'blender', menu, i)
                button_string = '        self.layout.row().operator("object.%s")\n' % stringcase.snakecase(button_name)
                if button_string not in menu_lines:
                    new_menu_lines.append(button_string)
                    remove_pass = True
                else:
                    print('Found button, skipping')

    read_write.save_text_lines(new_menu_lines, menu_file)


def get_last_button_number(menu_dict, software, menu):
    buttons = menu_dict[software][menu]
    biggest = 0
    for button in buttons:
        if button != 'order':
            num = buttons[button]['order']
            if num > biggest:
                biggest = num
    return biggest


def get_menu_at(menu_dict, software, menu, i):
    buttons = menu_dict[software][menu]
    for button in buttons:
        if button != 'order':
            if int(buttons[button]['order']) == i:
                return button


if __name__ == '__main__':
    # create_menu_file('TomTest', 'Tom Test', r'F:\FSU-CMPA\COMPANIES\_config\cgl_tools\blender\menus\TomTest\TomTest.py')
    # create_button_file('ButtonAaa', 'Button Aaa', 'TomTest')
    add_buttons_to_menu('TomTest')


