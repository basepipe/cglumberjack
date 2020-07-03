from cgl.plugins.CustomMenu import CustomMenu
import bpy


class LumberMenu(CustomMenu):
    def __init__(self, software='maya', type_='shelves'):
        CustomMenu.__init__(self, software, type_)

    def create_menu(self, name, menu_type='panel'):
        """
        creates a menu with title of 'name'
        :param name:
        :param menu_type:
        :return:
        """
        # load menu "name" from the blender name_panel.py file.
        # find the Panel class
        # panel_class = the one that has panel in it.
        # bpy.utils.register_class(panel_class)
        # from each class in that file:
        # add_button(button_class)
        print(name)

    def set_menu_parent(self):
        """
        set the parent of a menu
        :return:
        """
        pass

    def add_button(self, button_class):
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
        bpy.utils.register_class(LumbermillRigging)

    @staticmethod
    def find_menu_by_name(menu_name):
        """
        finds menu in software package given its string name
        :param parent:
        :param menu_name:
        :return:
        """
        # load menu "name" from the blender name_panel.py file.
        # return the class that matches "menu_name"
        return menu_class

    def delete_menu(self, menu_name):
        """
        deletes menu by "menu_name"
        :param shelf_name:
        :return:
        """
        menu_class = self.find_menu_by_name(menu_name)
        bpy.utils.unregister_class(menu_class)



