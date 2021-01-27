from cgl.plugins.preflight.preflight_check import PreflightCheck
from cgl.plugins.maya.alchemy import scene_object
import cgl.plugins.maya.tasks.lite as task_lite


class SubmitRender(PreflightCheck):

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
        so = scene_object()
        rendered = task_lite.submit_render_to_farm()
        self.pass_check('Check Passed')
