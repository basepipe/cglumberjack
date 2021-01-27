from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.lumbermill as lm
import cgl.plugins.maya.utils as utils
import os


class ReviewExists(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        """
        script to be executed when the preflight is run.

        If the preflight is successful:
        self.pass_check('Message about a passed Check')

        if the preflight fails:
        self.fail_check('Message about a failed check')
        :return:
        """
        s_o = lm.scene_object()
        if not os.path.exists(s_o.preview_path):
            lm.review()
        self.pass_check('Review Created/Exist, check passed!')
