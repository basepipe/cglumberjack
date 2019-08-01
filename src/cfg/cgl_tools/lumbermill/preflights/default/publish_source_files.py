from plugins.preflight.preflight_check import PreflightCheck
from cglcore.path import publish


class publish_source_files(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        path_object = self.shared_data['path_object']
        publish(path_object)
        self.pass_check('Stuff got published')

