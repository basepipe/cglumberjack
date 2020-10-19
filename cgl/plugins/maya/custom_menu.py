from cgl.plugins.CustomMenu import CustomMenu
import pymel.core as pm
import maya.mel


class MayaCustomMenu(CustomMenu):
    def __init__(self, software='maya', type_='shelves'):
        CustomMenu.__init__(self, software, type_)

    def get_scene_path(self):
        return pm.sceneName()

    def create_menu(self, name):
        shelf = pm.shelfLayout(name, parent=self.menu_parent)
        return shelf

    def set_menu_parent(self):
        name = maya.mel.eval('$tmpVar=$gShelfTopLevel')
        return pm.tabLayout(name, query=True, fullPathName=True)

    def add_button(self, shelf, label='', annotation='', command='', icon='', image_overlay_label=''):
        button_name = pm.shelfButton(image1=icon,
                                     parent=shelf,
                                     label=label,
                                     annotation=annotation,
                                     command=command,
                                     imageOverlayLabel=image_overlay_label)
        return button_name

    @staticmethod
    def find_menu_by_name(parent, menu_name):
        shelf_exists = pm.shelfLayout(menu_name, exists=True, parent=parent)
        shelf = None
        if shelf_exists:
            shelf = pm.shelfLayout(menu_name,
                                   query=True,
                                   fullPathName=True)
        return shelf

    def delete_menu(self, shelf_name):
        shelf_ = self.find_menu_by_name(self.menu_parent, shelf_name)
        if shelf_:
            pm.deleteUI(shelf_)



