from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.tasks.lay as lay
reload(lay)


class AddBundlesToLayout(PreflightCheck):

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
        success = lay.add_bundles_to_layout()
        if success:
            self.pass_check('All Bundles added to Layout, check passed')
        else:
            self.fail_check('Check Failed, Check Error Messages')
