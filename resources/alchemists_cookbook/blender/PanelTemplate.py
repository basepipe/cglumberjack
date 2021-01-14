import bpy


class PanelTemplate(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Panel Template'
    bl_label = bl_category

    def draw(self, context):
        """
        in here we'll have all the buttons for the Panel in the order that magic_browser saves them in.
        :param context:
        :return:
        """
        # ADD BUTTONS
        pass




