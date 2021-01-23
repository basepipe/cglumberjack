from cgl.plugins.preflight.preflight_check import PreflightCheck
# there is typically a lumbermill.py, and utils.py file in the plugins directory.
# look here for pre-built, useful functions
# from cgl.plugins.SOFTWARE import lumbermill
import cgl.plugins.maya.scene_description as sd
reload(sd)

class VersionUpLayout(PreflightCheck):

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
        layout_path = sd.export_layout()
        if layout_path:
            self.pass_check('Check Passed')
        else:
            self.fail_check('Layout export failed')
