import bpy


class ButtonTemplate(bpy.types.Operator):
    """
    This class is required to register a button in blender.
    """
    bl_idname = 'object.button_template'
    bl_label = 'button_template'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        run()


def run():
    """
    This run statement is what's executed when your button is pressed in blender.
    :return:
    """
    print('Hello World!: button_template')

