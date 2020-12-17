from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc
import bpy
from cgl.core.utils.read_write import load_json
from cgl.plugins.blender import magic_scene_description as msd

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object
            self.path_object = scene_object().copy(task = 'cam')

    def build(self):
        pass

    def _import(self, filepath = None, start_frame = 1000,**kwargs):
        from .anim import move_keyframes,get_keyframes
        from ..utils import set_framerange

        if not filepath:
            filepath = self.path_object.path_root

        camFile = alc.PathObject(filepath)
        print(788888888888888)
        print(filepath)

        fbx = camFile.copy(ext = 'fbx')
        json = camFile.copy(ext= 'json')
        camDic = load_json(json.path_root)



        # Imports the fbx for the published camera
        alc.import_file(filepath = fbx.path_root)
        camera = bpy.data.objects[camFile.shot]

        #Set Offset for the camera
        move_keyframes(camera,int(camDic[camFile.shot]['frame_start'])*-1)
        move_keyframes(camera,start_frame)
        start,end = get_keyframes(camera,ends=True)
        set_framerange(start,end)

        pass



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
    camDic = {}
    currentScene = alc.scene_object()

    # get all frames with assigned keyframes
    if camera == None:
        keyframes = alc.get_keyframes(get_selected_camera())

    else:
        keyframes = alc.get_keyframes(camera)

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
    alc.save_file()
    currentScene = alc.scene_object()
    framerange = alc.get_framerange()

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

    alc.set_framerange(camDic[camera.name]['frame_start'],
                      camDic[camera.name]['frame_end'])

    if fbx:
        alc.export_selected(camFbxPath.path_root)

    alc.save_file_as(camTask.path_root)
    alc.open_file(currentScene.path_root)

    # print(camFbxPath.path_root)
    # bpy.ops.export_scene.fbx(filepath = camFbxPath.path_root, use_selection = True)


