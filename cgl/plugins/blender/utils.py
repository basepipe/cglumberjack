import re
import os
import sys
import stringcase
import logging
import bpy
import cgl.core.utils.read_write as read_write
from cgl.ui.widgets.dialog import InputDialog
from cgl.apps.pipeline.utils import get_button_path, get_menu_path
from cgl.core.path import get_resources_path
from cgl.core.project import get_cgl_tools

logger = logging.getLogger('qtutils')





class QtWindowEventLoop(bpy.types.Operator):
    """Allows PyQt or PySide to run inside Blender"""
    # example taken from https://github.com/vincentgires/blender-scripts/blob/master/scripts/addons/qtutils/core.py

    bl_idname = 'screen.qt_event_loop'
    bl_label = 'Qt Event Loop'

    def __init__(self, widget, *args, **kwargs):
        self._widget = widget
        self._args = args
        self._kwargs = kwargs

    def modal(self, context, event):
        wm = context.window_manager

        if not self.widget.isVisible():
            # if widget is closed
            logger.debug('finish modal operator')
            wm.event_timer_remove(self._timer)
            return {'FINISHED'}
        else:
            logger.debug('process the events for Qt window')
            self.event_loop.processEvents()
            self.app.sendPostedEvents(None, 0)

        return {'PASS_THROUGH'}

    def execute(self, context):
        logger.debug('execute operator')

        self.app = QtWidgets.QApplication.instance()
        # instance() gives the possibility to have multiple windows
        # and close it one by one

        if not self.app:
            # create the first instance
            self.app = QtWidgets.QApplication(sys.argv)

        if 'stylesheet' in self._kwargs:
            stylesheet = self._kwargs['stylesheet']
            self.set_stylesheet(self.app, stylesheet)

        self.event_loop = QtCore.QEventLoop()
        self.widget = self._widget(*self._args, **self._kwargs)

        logger.debug(self.app)
        logger.debug(self.widget)

        # run modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(1 / 120, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def set_stylesheet(self, app, filepath):
        file_qss = QtCore.QFile(filepath)
        if file_qss.exists():
            file_qss.open(QtCore.QFile.ReadOnly)
            stylesheet = QtCore.QTextStream(file_qss).readAll()
            app.setStyleSheet(stylesheet)
            file_qss.close()


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


