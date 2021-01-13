import os
import bpy
import importlib
from cgl.plugins.CustomMenu import CustomMenu
from .utils import get_button_path, get_menu_path
from cgl.core.config.config import ProjectConfig


class LumberMenu(CustomMenu):
    def __init__(self, software='blender', type_='menus'):
        CustomMenu.__init__(self, software, type_)
        self.cfg = ProjectConfig()

    def create_menu(self, name, menu_type='panel'):
        """
        creates a menu with title of 'name'
        :param name:
        :param menu_type:
        :return:
        """
        menu_class = self.find_menu_by_name(name)
        try:
            bpy.utils.register_class(menu_class)
        except ValueError:
            print('%s already registered' % name)

    def add_button(self, menu, label, annotation='', command='', icon='', image_overlay_label='', hot_key=''):
        """
        add a button to a menu
        :param menu:
        :param label:
        :param annotation:
        :param command:
        :param icon: not required
        :param image_overlay_label: not required
        :param hot_key: not required
        :return:
        """
        menu_path = get_button_path('blender', menu, label, cfg=self.cfg)
        module = menu_path.split('cookbook\\')[-1].replace('\\', '.').replace('.py', '')
        module = 'cookbook.%s' % module
        try:
            module_result = importlib.import_module(module)
            button_class = getattr(module_result, label)
            try:
                bpy.utils.register_class(button_class)
            except ValueError:
                print('%s already registered' % label)
        except ModuleNotFoundError:
            print('module: {0} not found'.format(module))


    def find_menu_by_name(self, menu_name):
        """
        finds menu in software package given its string name
        :param parent:
        :param menu_name:
        :return:
        """
        if isinstance(menu_name, dict):
            menu_name = menu_name['name']
        print(11111111111111)
        print(self.cfg.cookbook_folder)
        menu_path = get_menu_path('blender', menu_name, menu_file=True, cfg=self.cfg)
        module = menu_path.split('cookbook\\')[-1].replace('\\', '.').replace('.py', '')
        module = 'cookbook.%s' % module
        print(222222222222)
        print(module)
        module_result = importlib.import_module(module)
        menu_class = getattr(module_result, menu_name)
        return menu_class

    def delete_menu(self, menu_name):
        """
        deletes menu by "menu_name"
        :param menu_name:
        :return:
        """
        menu_class = self.find_menu_by_name(menu_name)
        try:
            bpy.utils.unregister_class(menu_class)
        except RuntimeError:
            print('bpy.utils.unregister_class could not find {0}'.format(menu_class))



