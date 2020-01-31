from plugins.preflight.preflight_check import PreflightCheck


class CreateExrProxy(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        self.shared_data['publish_path_object'].make_proxy(ext='exr')
        self.pass_check('Check Passed')

