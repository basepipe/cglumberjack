import os
import pymel.core as pm
from .smart_task import SmartTask
from cgl.plugins.maya.alchemy import PathObject, scene_object
from cgl.core.config import app_config
from cgl.ui.widgets.dialog import MagicList, InputDialog, FrameRange
from cgl.plugins.maya.utils import get_shape_name, load_plugin
import cgl.plugins.maya.msd as msd
reload(msd)
try:
    import pymel.core as pm
    import maya.mel as mel
except ModuleNotFoundError:
    print('Skipping pymel.core - outside of maya')

TASKNAME = os.path.basename(__file__).split('.py')[0]


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            self.path_object = scene_object()

    def _import(self, filepath):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        from cgl.plugins.maya.alchemy import reference_file
        reference_file(filepath=filepath)

    def import_latest(self):
        """
        imports the latest camera for a shot.
        :param seq: sequence
        :param shot: shot
        :param ext:
        :return:
        """
        cam_path = get_latest()
        if os.path.exists(cam_path):
            self._import(cam_path)
        else:
            print('Could not find camera at {}'.format(cam_path))


def get_latest(ext='mb'):
    this_obj = scene_object().copy(task='cam', context='render',
                                   user='publish', latest=True, set_proper_filename=True, ext=ext)
    return this_obj.path_root


def main_import(filepath):
    """

    :param filepath:
    :return:
    """
    pass


def _publish(path_object):
    """

    :param path_object:
    :return:
    """
    pass


class RenameCameraDialog(MagicList):
    """
    this is very specific to 3d cameras
    """

    def __init__(self, parent=None, title=None, list_items=None, regex=None, name_example=None, scene_obj=None):
        MagicList.__init__(self, parent, list_items=list_items, title=title, buttons=['Rename Selected'])
        self.regex = regex
        self.name_example = name_example
        self.path_object = scene_obj
        self.cam_name = 'cam%s_%s' % (self.path_object.seq, self.path_object.shot)
        self.rename_it = None
        self.selected = []
        self.title = title
        self.item_selected.connect(self.on_item_selected)
        self.button_signal.connect(self.on_button_clicked)

    def on_item_selected(self, data):
        self.selected = data

    def on_button_clicked(self):
        for each in self.selected:
            each = each[0]
            names = []
            if '|' in each:
                names = each.split('|')[-1]
                child_name = names[-1]
            else:
                child_name = each
            if self.cam_name:
                child_name = self.cam_name
            message = '%s does not pass\n%s' % (child_name, self.name_example)
            self.rename_it = InputDialog(title=self.title, message=message, buttons=['Rename', 'Cancel'],
                                         line_edit=True, line_edit_text=child_name,
                                         regex=self.regex, name_example=self.name_example)
            self.rename_it.exec_()
            if self.rename_it.button == 'Rename':
                if names:
                    names[-1] = self.rename_it.line_edit.text()
                    new_name = '|'.join(names)
                else:
                    new_name = self.rename_it.line_edit.text()
                    print('renaming %s to %s' % (each, new_name))
                pm.rename(each, new_name)
        self.close()


def get_camera_names(visible=True, renderable=False):
    ignore = ['persp', 'top', 'right', 'left', 'bottom']
    cameras = pm.ls(ca=True, v=visible)
    cams = []
    render_cams = []
    for each in cameras:
        if each not in ignore:
            pm.select(each)
            if renderable:
                if pm.getAttr('%s.renderable' % each):
                    render_cams.append(str(each))
            topnode = pm.pickWalk(d='up')[0]
            shapenode = get_shape_name(topnode)
            o_type = pm.objectType(shapenode)
            if o_type == 'camera':
                cams.append(str(topnode))
    if renderable:
        return render_cams
    return cams


def publish_selected_camera(camera=None, mb=True, abc=False, fbx=True, shotgun=False):

    if camera:
        pm.select(d=True)
        pm.select(camera)
    try:
        selection = pm.ls(sl=True)[0]
        if selection:
            s_obj = scene_object()
            seq_, shot_ = selection.name().split('_')
            seq_ = seq_.replace('cam', '')
            cam_obj = s_obj.copy(shot=shot_, seq=seq_, task='cam', user='publish', context='render',
                                 latest=True, set_proper_filename=True)
            pub_obj = cam_obj.next_major_version()
            next_pub_source_version = pub_obj.copy(context='source').path_root
            next_pub_output_version = pub_obj.path_root
            fbx_output = pub_obj.copy(ext='fbx').path_root
            abc_output = pub_obj.copy(ext='abc').path_root
            # make dirs if they don't exist
            if not os.path.exists(os.path.dirname(next_pub_source_version)):
                os.makedirs(os.path.dirname(next_pub_source_version))
            if not os.path.exists(os.path.dirname(next_pub_output_version)):
                os.makedirs(os.path.dirname(next_pub_output_version))
            #
            sframe, eframe, minframe, maxframe = set_shot_frame_range('%s_%s' % (seq_, shot_),
                                                                      project=scene_object().project)
            if mb:
                pm.exportSelected(next_pub_source_version, typ='mayaBinary')
                pm.exportSelected(next_pub_output_version, typ='mayaBinary')
            if fbx:
                export_fbx(fbx_output, start_frame=sframe, end_frame=eframe)
            if abc:
                export_abc(abc_output, start_frame=sframe, end_frame=eframe)
            msd.CameraDescription(mesh_name=camera, start_frame=sframe, end_frame=eframe, handle_start=minframe,
                                  handle_end=maxframe).export()
    except IndexError:
        print('No Camera Selected')


def export_fbx(filepath, start_frame=False, end_frame=False):
    load_plugin('fbxmaya')
    if not start_frame:
        start_frame = int(pm.playbackOptions(query=True, animationStartTime=True))
    if not end_frame:
        end_frame = int(pm.playbackOptions(query=True, animationEndTime=True))
    if start_frame:
        command = 'FBXExportBakeComplexAnimation -v true; FBXExportInputConnections -v false; ' \
                   'FBXExportBakeComplexEnd -v %s; FBXExportBakeComplexStart -v %s; FBXExport -f "%s" -s' \
                   % (str(int(end_frame)), str(int(start_frame)), filepath)
        mel.eval(command)
    else:
        pm.exportSelected(filepath, typ='FBX export')


def export_abc(filepath, start_frame=False, end_frame=False):
    load_plugin('AbcExport')
    load_plugin('AbcImport')
    command = 'AbcExport -j "-frameRange %s %s -uvWrite -uvWrite -worldSpace -attrPrefix pxm' \
              '  -attrPrefix PXM -dataFormat ogawa  -sl  -file %s";' \
              % (start_frame, end_frame, filepath)
    mel.eval(command)


def set_shot_frame_range(shot_name, project):
    # throw up the Frame Range Dialog
    sframe = int(pm.playbackOptions(query=True, animationStartTime=True))
    eframe = int(pm.playbackOptions(query=True, animationEndTime=True))
    minframe = int(pm.playbackOptions(query=True, min=True))
    maxframe = int(pm.playbackOptions(query=True, max=True))
    dialog2 = FrameRange(sframe=sframe,
                         eframe=eframe,
                         minframe=minframe,
                         maxframe=maxframe,
                         message='Optional: Set Shotgun Frame Range for %s' % shot_name,
                         both=True)
    dialog2.exec_()
    total_frames = int(dialog2.eframe)-int(dialog2.sframe)
    return dialog2.sframe, dialog2.eframe, dialog2.minframe, dialog2.maxframe


