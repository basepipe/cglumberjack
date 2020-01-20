from plugins.CustomMenu import CustomMenu


class BlenderCustomMenu(CustomMenu):
    def __init__(self, software='maya', type_='shelves'):
        CustomMenu.__init__(self, software, type_)

    def get_scene_path(self):
        """
        Returns the current scene path
        :return:
        """
        pass

    def create_menu(self, name):
        """
        Creates a menu with the name "name", returns the resulting menu
        :param name: name of the menu
        :return: menu
        """
        menu = "Creates a menu called name"
        return menu

    def set_menu_parent(self):
        """
        This is the object we will attach our menu to.
        :return:
        """
        pass

    def add_button(self, shelf, label='', annotation='', command='', icon='', image_overlay_label=''):
        """
        command to add a button to a menu
        :param shelf: the menu or shelf to add the button to
        :param label: label of the button
        :param annotation: information about the button
        :param command: command to execute
        :param icon: location of the icon
        :param image_overlay_label:
        :return:
        """
        pass

    @staticmethod
    def find_menu_by_name(parent, menu_name):
        """
        Finds a menu object by the given menu_name
        :param parent:
        :param menu_name:
        :return:
        """
        pass

    def delete_menu(self, menu_name):
        """
        Deletes the menu of name "menu_name"
        :param shelf_name:
        :return:
        """
        pass



