from cgl.plugins.preflight.preflight_check import PreflightCheck
from cgl.plugins.maya import alchemy

class Publish(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        path_object = alchemy.publish()
        print(path_object.path_root)
        self.pass_check('Version  Published!')
        alchemy.confirm_prompt(title='Publish Successful!', message='Version %s has been published!\n '
                                                                       'you may close this scene' % path_object.version)



