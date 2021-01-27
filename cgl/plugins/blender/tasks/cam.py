from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc
import bpy
from cgl.core.utils.read_write import load_json
from cgl.plugins.blender import msd

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object

            self.path_object = scene_object().copy(task='cam',
                                                   latest=True,
                                                   user = 'publish',
                                                   context = 'render',
                                                   set_proper_filename=True)

    def build(self):
        pass

    def _import(self, filepath = None, start_frame = 1000,**kwargs):
        from .anim import move_keyframes,get_keyframes
        from ..utils import set_framerange, parent_object, get_object,get_layer
        from cgl.plugins.blender.alchemy import scene_object ,import_file
        from cgl.core.path import PathObject

        if not filepath:
            filepath = self.path_object.path_root

        camFile = PathObject(filepath)


        fbx = camFile.copy(ext = 'fbx')
        json = camFile.copy(ext= 'json')
        camDic = load_json(json.path_root)
        scene = scene_object()

        # Imports the fbx for the published camera
        camera = import_file(filepath = fbx.path_root,namespace=scene.shot)
        #camera = bpy.data.objects[camFile.shot]

        #Set Offset for the camera
        move_keyframes(camera,int(camDic[camFile.shot]['frame_start'])*-1)
        move_keyframes(camera,start_frame)
        camera_keyframes = get_keyframes(camera,ends=True)
        start,end = camera_keyframes


        layer_group = get_layer('MAIN')
        parent_object(camera,layer_group)
        set_framerange(start,end)
        
        set_shot_from_camera(cam = camera)

        pass

    def _remove(self,**kwargs):
        from ..utils import delete_object
        delete_object("{}:cam".format(self.path_object.shot))


def set_shot_from_camera(cam = None):
    import bpy 

    for area in bpy.context.screen.areas:
        if area.type == 'DOPESHEET_EDITOR':
            for region in area.regions:
                if region.type == 'WINDOW':
                    ctx = bpy.context.copy()
                    ctx['area'] = area
                    ctx['region'] = region
                    ctx['mode'] = 'TIMELINE'
                    bpy.ops.action.view_all(ctx)

    bpy.ops.object.select_by_type(type='CAMERA')

    if cam == None:
        cam = bpy.context.selected_objects[0]
        cam.select_set(state=True)
        
    bpy.context.view_layer.objects.active = cam

    bpy.context.scene.camera = bpy.context.scene.objects[cam.name]

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            
def get_selected_camera():
    camera = bpy.context.object

    if camera.type == 'CAMERA':
        cam_object = camera
        return (cam_object)

    else:
        print('object isnt camera')
        return

    # get keyframes of object list

def return_camera_dictionary(camera=None):
    from cgl.plugins.blender.tasks.anim import get_keyframes
    camDic = {}
    currentScene = alc.scene_object()

    # get all frames with assigned keyframes
    if camera == None:
        keyframes = get_keyframes(get_selected_camera())

    else:
        keyframes = get_keyframes(camera)

    frame_start, frame_end = keyframes[0], keyframes[-1]

    camDic[camera.name] = {'shot': camera.name,
                           'frame_start': frame_start,
                           'frame_end': frame_end,
                           'source_layout': currentScene.path}

    return camDic

def check_cam_export_directory(camTask):
    from os import makedirs
    from os.path import isdir

    camTask = camTask.next_major_version()
    source = camTask.copy(filename='', context='source')
    render = camTask.copy(filename='', context='render')
    for camera in (source, render):
        makedirs(camera.path_root)
        print(camera.path_root)
    return camTask

def publish_selected_camera(camera=None, mb=True, abc=False, fbx=False, unity=False, shotgun=True, json=False):

    from cgl.core.utils.read_write import save_json
    from cgl.plugins.blender.utils import  get_framerange, set_framerange
    alc.save_file()
    currentScene = alc.scene_object()
    framerange = get_framerange()

    # Finds the start and end frame of the given camera
    camDic = return_camera_dictionary(camera)

    # Defines the shot object base of the camera name
    shotName = alc.scene_object().copy(shot=camera.name)

    # Defines cam task , cam directory, fbx , json
    camTask = shotName.copy(task='cam',
                            user='publish',
                            latest=True,
                            set_proper_filename=True)

    camTask = check_cam_export_directory(camTask)
    camFbxPath = camTask.copy(ext='fbx', context='render')
    camJsonPath = camTask.copy(ext='json', context='render')

    save_json(camJsonPath.path_root, camDic)

    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    camera.select_set(True)

    set_framerange(camDic[camera.name]['frame_start'],
                      camDic[camera.name]['frame_end'])

    if fbx:
        alc.export_selected(camFbxPath.path_root)

    alc.save_file_as(camTask.path_root)
    alc.open_file(currentScene.path_root)

    # print(camFbxPath.path_root)
    # bpy.ops.export_scene.fbx(filepath = camFbxPath.path_root, use_selection = True)


def get_msd_info(camera=None):
    from cgl.plugins.blender.tasks.anim import get_keyframes
    camDic = {}
    currentScene = alc.scene_object()

    # get all frames with assigned keyframes
    if camera == None:
        keyframes = get_keyframes(get_selected_camera())

    else:
        keyframes = get_keyframes(camera)

    frame_start, frame_end = keyframes[0], keyframes[-1]

    camDic[camera.name] = {'shot': camera.name,
                           'frame_start': frame_start,
                           'frame_end': frame_end,
                           'source_layout': currentScene.path}

    return camDic