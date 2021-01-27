import re
from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.utils as utils
import cgl.plugins.maya.tasks.cam as task_cam
reload(task_cam)
from cgl.plugins.maya.lumbermill import scene_object
import cgl.ui.widgets.dialog as dialog
from cgl.core.config import app_config


class PublishCameras(PreflightCheck):
    cams = []
    invalid_cams = []
    dialog = None
    invalid_dialog = None
    regex = ''
    cam_example = ''

    def getName(self):
        pass

    def run(self):
        utils.remove_namespace('cam')
        print('regex:', app_config()['rules']['general']['shot_cam']['regex'])
        self.regex = re.compile(r'%s' % app_config()['rules']['general']['shot_cam']['regex'])
        self.cam_example = app_config()['rules']['general']['shot_cam']['example']
        # example = app_config()['paths']['rules']['shot_cam_example']
        self.get_cams()
        if self.invalid_cams:
            self.invalid_dialog = task_cam.RenameCameraDialog(title="Bad Camera Names", regex=self.regex,
                                                    name_example=self.cam_example,
                                                    list_items=self.invalid_cams, scene_obj=scene_object())
            self.invalid_dialog.exec_()

        if self.cams:
            self.dialog = dialog.MagicList(title='Cameras to Export',
                                             combo_box=['.mb', '.fbx', '.abc', '.json', 'all'], combo=True,
                                             combo_label='Export Type(s)',
                                             buttons=['Publish Selected', 'Publish All'],
                                             list_items=self.cams,
                                             button_functions=[self.publish_selected, self.publish_all])
            self.dialog.combo.setCurrentIndex(1)
            self.dialog.exec_()

    def get_cams(self):
        all_cams = task_cam.get_camera_names()
        self.cams = []
        self.invalid_cams = []
        for each in all_cams:
            if re.search(self.regex, each):
                self.cams.append(each)
            else:
                self.invalid_cams.append(each)

    def ignore_naming(self):
        self.invalid_dialog.accept()

    def publish_selected(self):
        mb = True
        abc = True
        fbx = True
        json = True
        print('selection')
        print(self.dialog.selection)
        current = self.dialog.combo.currentIndex()
        if current == 5:
            mb = True
            abc = True
            fbx = True
            json = True
        if current == 4:
            json = True
        if current == 3:
            abc = True
        if current == 2:
            fbx = True
        if current == 1:
            mb = True
        for cam in self.dialog.selection:
            task_cam.publish_selected_camera(cam[0], mb=mb, abc=abc, fbx=fbx)
            self.pass_check('Camera Published!')
            shot_name = cam[0].replace('cam', '')
            print 'Shot: %s head in and tail out set' % shot_name
        print 'Close %s' % self.dialog
        self.dialog.accept()
        self.dialog.close()

    def publish_all(self):
        for each in self.cams:
            task_cam.publish_selected_camera(each, mb=True, abc=False, fbx=True)
        self.pass_check('Cameras Published!')
        self.dialog.close()


if __name__ == "__main__":
    pass
