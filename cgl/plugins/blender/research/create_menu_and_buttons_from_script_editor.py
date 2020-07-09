import bpy


class Lumbermill_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Lumbermill'
    bl_label = 'Lumbermill'

    def draw(self, context):
        self.layout.row().operator('object.launch_lumbermill')
        self.layout.row().operator('object.version_up')
        self.layout.row().operator('object.create_turntable')
        self.layout.row().operator('object.clean_turntable')
        # self.layout.row().operator('object.render')
        self.layout.row().operator('object.review')
        self.layout.row().operator('object.publish')


class Render(bpy.types.Operator):
    bl_idname = 'object.render'
    bl_label = 'render'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print(self.bl_label)


class Review(bpy.types.Operator):
    bl_idname = 'object.review'
    bl_label = 'Review'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print(self.bl_label)


class Publish(bpy.types.Operator):
    bl_idname = 'object.publish'
    bl_label = 'Publish'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print(self.bl_label)


class CleanTurntable(bpy.types.Operator):
    bl_idname = 'object.clean_turntable'
    bl_label = 'Clean Turntable'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print(self.bl_label)


class CreateTurntable(bpy.types.Operator):
    bl_idname = 'object.create_turntable'
    bl_label = 'Create Turntable'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print(self.bl_label)


class LaunchLumbermill(bpy.types.Operator):
    bl_idname = 'object.launch_lumbermill'
    bl_label = 'Launch Lumbermill'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print(self.bl_label)


class VersionUp(bpy.types.Operator):
    bl_idname = 'object.version_up'
    bl_label = 'Version Up'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LumbermillRigging)
    bpy.utils.register_class(VersionUp)
    bpy.utils.register_class(LaunchLumbermill)
    bpy.utils.register_class(Render)
    bpy.utils.register_class(Review)
    bpy.utils.register_class(Publish)
    bpy.utils.register_class(CreateTurntable)
    bpy.utils.register_class(CleanTurntable)


def unregister():
    bpy.utils.unregister_class(LumbermillRigging)
    bpy.utils.unregister_class(CreateCube)


if __name__ == '__main__':
    register()