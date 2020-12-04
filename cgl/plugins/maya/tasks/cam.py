import os
import pymel.core as pm
from .smart_task import SmartTask
from cgl.plugins.maya.lumbermill import LumberObject, scene_object
from cgl.core.config import app_config
from cgl.ui.widgets.dialog import MagicList, InputDialog
from cgl.plugins.maya.utils import get_shape_name, set_shot_frame_range, export_abc, export_fbx
import cgl.plugins.maya.scene_description as sd
reload(sd)

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
        pass

    def import_latest(self, seq, shot, ext='mb'):
        """
        imports the latest camera for a shot.
        :param seq: sequence
        :param shot: shot
        :param ext:
        :return:
        """
        this_obj = scene_object().copy(task=TASKNAME, seq=seq, shot=shot, context='render',
                                       user='publish', latest=True, set_proper_filename=True, ext=ext)
        if os.path.exists(this_obj.path_root):
            self._import(filepath=this_obj.path_root)
        else:
            print('Could not glob layout path at {}'.format(this_obj.path))


def get_latest(seq, shot, task=TASKNAME, ext='mb'):
    this_obj = scene_object().copy(task=TASKNAME, seq=seq, shot=shot, context='render',
                                   user='publish', latest=True, set_proper_filename=True, ext=ext)
    return this_obj


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

    def on_item_selected(self, data):
        print(data)

    def on_button_clicked(self):
        for each in self.selected:
            names = []
            if '|' in each:
                names = each.split('|')
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


def publish_selected_camera(camera=None, mb=True, abc=False, fbx=False, unity=False, shotgun=True, json=False):

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
            json_path = pub_obj.copy(ext='json').path_root
            # print(next_pub_output_version)
            # print(fbx_output)
            # print(abc_output)
            # print(json_path)

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
            # if fbx:
            #     export_fbx(fbx_output, start_frame=sframe, end_frame=eframe)
            # if abc:
            #     export_abc(abc_output, start_frame=sframe, end_frame=eframe)
            if json:
                sd.create_camera_description(camera=selection, frame_start=sframe, frame_end=eframe,
                                             handle_start=minframe,
                                             handle_end=maxframe, add_to_scene_layout=True)
    except IndexError:
        print('No Camera Selected')




