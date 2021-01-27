from cgl.plugins.preflight.preflight_check import PreflightCheck
from cgl.plugins.maya import utils
reload(utils)


class UpdateReferences(PreflightCheck):

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
        utils.update_all_references()
        self.pass_check('Check Passed')
        # self.fail_check('Check Failed')
