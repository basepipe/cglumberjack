"""
This script will submit current file to deadline for render
"""
import os
from datetime import datetime
import sys
import subprocess
# noinspection PyUnresolvedReferences
import maya.cmds as cmds
# noinspection PyUnresolvedReferences
import pymel.core as pm
from cgl.core.path import PathObject
import cgl.plugins.maya.alchemy as lm
from cgl.plugins.maya.tasks.cam import get_camera_names
from cgl.plugins.maya.tasks.lite import get_render_folder
from cgl.core.utils.general import current_user
from cgl.ui.widgets.dialog import InputDialog


PATH_OBJECT = lm.scene_object()
JOB_NAME = '%s_%s_%s_%s' % (PATH_OBJECT.seq, PATH_OBJECT.shot, PATH_OBJECT.task, PATH_OBJECT.version)
FILE_NAME = '%s_%s_%s' % (PATH_OBJECT.seq, PATH_OBJECT.shot, PATH_OBJECT.task)
RENDER_PATH = get_render_folder()
CURRENT_LAYER = str(pm.nodetypes.RenderLayer.currentLayer())


def create_plugin_info_file(unc=True, render_layer=CURRENT_LAYER):
    """
    this function will collect scene file information and write a job file
    :return:
    """
    ignore_cams = ['persp', 'top', 'right', 'left', 'bottom']
    scene_file = pm.sceneName()
    render_path = RENDER_PATH
    job_object = PATH_OBJECT.copy(context='source', filename='pluginInfo_%s' % render_layer, ext='job')
    plugin_file = job_object.path_root
    # if unc:
    #     render_path = get_unc_filepath(RENDER_PATH)
    #     scene_file = get_unc_filepath(scene_file)

    renderer_name = 'arnold'
    version = cmds.about(version=True)
    project_path = ''
    width = pm.getAttr("defaultResolution.width")
    height = pm.getAttr("defaultResolution.height")
    output_file_prefix = FILE_NAME
    renderable_cameras = get_camera_names(renderable=True)
    if not renderable_cameras:
        print(renderable_cameras)
        dialog = InputDialog(message="No renderable cameras found - please check camera settings")
        dialog.exec_()
    if ':' in renderable_cameras[0]:
        base_camera = renderable_cameras[0].split(':')[-1]
    else:
        print(renderable_cameras)
        base_camera = renderable_cameras[0]
    current_layer = render_layer
    output_file_path = render_path
    print(output_file_path)
    if len(renderable_cameras) > 1:
        output_file_path = render_path
        print('Multiple cameras, going to have to hard code some stuff now')
    cam_dict = {'camera': '',
                'camera0': '',
                'camera1': '',
                'camera2': '',
                'camera3': '',
                'camera4': '',
                'camera5': '',
                'camera6': '',
                'camera7': ''
                }
    for i, each in enumerate(renderable_cameras):
        print(i, each)
        camera_name = 'camera%s' % i
        if each not in ignore_cams:
            cam_dict[camera_name] = each

    settings = {'Animation': 1,
                'RenderSetupIncludeLights': 1,
                'Renderer': renderer_name,
                'UsingRenderLayers': 1,
                'RenderLayer': current_layer,
                'RenderHalfFrames': 0,
                'FrameNumberOffset': 0,
                'LocalRendering': 0,
                'StrictErrorChecking': True,
                'MaxProcessors': 0,
                'ArnoldVerbose': 2,
                'MayaToArnoldVersion': 3,
                'Version': version,
                'UseLegacyRenderLayers': 0,
                'Build': '64 bit',
                'ProjectPath': project_path,
                'StartupScript': '',
                'ImageWidth': width,
                'ImageHeight': height,
                'OutputFilePath': output_file_path,
                'OutputFilePrefix': output_file_prefix,
                'Camera': cam_dict['camera0'],
                'Camera0': cam_dict['camera1'],
                'Camera1': cam_dict['camera2'],
                'Camera2': cam_dict['camera3'],
                'Camera3': cam_dict['camera4'],
                'Camera4': cam_dict['camera5'],
                'Camera5': cam_dict['camera6'],
                'Camera6': cam_dict['camera7'],
                'CountRenderableCameras': 1,
                'SceneFile': scene_file,
                'IgnoreError211': 0,
                'UseLocalAssetCaching': 0,
                'EnableOpenColorIO': 0
                }
    
    write_keys(settings, plugin_file)
    return plugin_file


def write_keys(keypairs, keyfile):
    string = ''
    for key in keypairs:
        # print '%s=%s\n' % (key, keypairs[key])
        string += '%s=%s\n' % (key, keypairs[key])
    with open(keyfile, 'w') as f:
        f.write(string)
    return keyfile


def create_job_info_file(job_name=JOB_NAME, comment='', dept=PATH_OBJECT.task, frange=None, group='none',
                         output_dir=RENDER_PATH, output_file_name='testthing.####.exr',
                         render_layer=CURRENT_LAYER):
    if not frange:
        frange = get_frange()
    job_object = PATH_OBJECT.copy(context='source', filename='jobInfo_%s' % render_layer, ext='job')
    job_info_file = job_object.path_root
    now = datetime.now()
    date_time = str(now.strftime("%d/%m/%Y %H:%M"))
    settings = {'Name': job_name,
                'UserName': current_user(),
                'Region': '',
                'Comment': comment,
                'Department': dept,
                'Frames': frange,
                'Group': group,
                'Blacklist': '',
                'ScheduledStartDateTime': date_time,
                'OverrideTaskExtraInfoNames': False,
                'MachineName': '',
                'Plugin': 'MayaBatch',
                'OutputDirectory0': output_dir,
                'OutputFilename0': output_file_name,
                'EventOptIns': ''
                }

    write_keys(settings, job_info_file)
    return job_info_file


def get_frange():
    sframe = int(pm.getAttr('defaultRenderGlobals.fs'))
    eframe = int(pm.getAttr('defaultRenderGlobals.ef'))
    return '%s-%s' % (sframe, eframe)


def maya_deadline_info(job_name=JOB_NAME, comment='Default Comment', output_file=RENDER_PATH,
                       initial_status='Suspended', dept=PATH_OBJECT.task, unc=True):
    """
    this function will collect maya deadline information and write a job file
    :return:
    """
    # # test = r'C:/Users/raijv/Documents/maya/projects/default/images/masterLayer_2.iff.????'
    # if unc:
    #     output_file = get_unc_filepath(output_file)

    maya_deadline_object = PATH_OBJECT.copy(context='render', filename='maya_deadline_info', ext='job')
    maya_deadline_info_file = maya_deadline_object.path_root
    sframe = int(pm.getAttr('defaultRenderGlobals.startFrame'))
    eframe = int(pm.getAttr('defaultRenderGlobals.endFrame'))
    frange = '%s-%s' % (sframe, eframe)

    info_txt = 'Plugin=MayaBatch\n' \
               'Name=%s\n' \
               'Comment=%s\n' \
               'Pool=none\n' \
               'MachineLimit=0\n' \
               'Priority=50\n' \
               'OnJobComplete=Nothing\n' \
               'TaskTimeoutMinutes=0\n' \
               'MinRenderTimeMinutes=0\n' \
               'ConcurrentTasks=1\n' \
               'Department=%s\n' \
               'Group=none\n' \
               'LimitGroups=\n' \
               'JobDependencies=\n' \
               'InitialStatus=%s\n' \
               'OutputFilename0=%s\n' \
               'Frames=%s\n' \
               'ChunkSize=1' % (job_name, comment, dept, initial_status, output_file, frange)

    with open(maya_deadline_info_file, 'w') as job_file:
        print('Saving Deadline Info file to %s' % maya_deadline_info_file)
        job_file.write(info_txt)
    return maya_deadline_info_file


def get_unc_filepath(file_path, root_dir='Z:'):
    file_path = file_path.replace('/', '\\')
    return file_path.replace(root_dir, r'\\cmpa-w-fs04.film.fsu.edu\TestShare')


def submit_to_deadline(render_layer=str(pm.nodetypes.RenderLayer.currentLayer())):
    """
    this function will send current scene to deadline for rendering
    :return:
    """
    deadline_cmd = r"C:\PROGRA~1\Thinkbox\Deadline10\bin\deadlinecommand.exe"
    job_file = create_job_info_file(render_layer=render_layer)
    info_file = create_plugin_info_file(render_layer=render_layer)
    command = '%s "%s" "%s"' % (deadline_cmd, job_file, info_file)
    print(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(process.stdout.readline, b"")
    for line in lines_iterator:
        print(line)
        sys.stdout.flush()


