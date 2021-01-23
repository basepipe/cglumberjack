from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.tasks.lite as task_lite


class PublishLightRig(PreflightCheck):

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
        task_lite.publish_light_rig()
        self.pass_check('Check Passed')

