from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_gif_proxy, create_gif_thumb


class CreateGif(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        create_gif_proxy(self.shared_data['hdProxy'])
        create_gif_thumb(self.shared_data['hdProxy'])
        self.pass_check('Check Passed: Gif Created!')
        # self.fail_check('Check Failed')

