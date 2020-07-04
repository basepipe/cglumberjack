import bpy
import importlib
from cgl.plugins.CustomMenu import CustomMenu
from cgl.plugins.blender.utils import get_menu_path, get_button_path


class LumberMenu(CustomMenu):
    def __init__(self, software='blender', type_='menus'):
        CustomMenu.__init__(self, software, type_)

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
        :param shelf:
        :param label:
        :param annotation:
        :param command:
        :param icon:
        :param image_overlay_label:
        :return:
        """
        menu_path = get_button_path('blender', menu, label)
        module = menu_path.split('cgl_tools\\')[-1].replace('\\', '.').replace('.py', '')
        module = 'cgl_tools.%s' % module
        module_result = importlib.import_module(module)
        button_class = getattr(module_result, label)
        try:
            bpy.utils.register_class(button_class)
        except ValueError:
            print('%s already registered' % label)

    @staticmethod
    def find_menu_by_name(name):
        """
        finds menu in software package given its string name
        :param parent:
        :param menu_name:
        :return:
        """
        menu_path = get_menu_path('blender', name, menu_file=True)
        module = menu_path.split('cgl_tools\\')[-1].replace('\\', '.').replace('.py', '')
        module = 'cgl_tools.%s' % module
        module_result = importlib.import_module(module)
        menu_class = getattr(module_result, name)
        return menu_class

    def delete_menu(self, menu_name):
        """
        deletes menu by "menu_name"
        :param shelf_name:
        :return:
        """
        menu_class = self.find_menu_by_name(menu_name)
        bpy.utils.unregister_class(menu_class)



