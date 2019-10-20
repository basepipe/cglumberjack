from plugins.preflight.preflight_check import PreflightCheck
from cglcore.convert import create_mov


class CreateMOV(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # get the sequence to be converted
        for r in self.shared_data['render_paths']:
            create_mov(r)
        self.pass_check('Movie Created!')
        
        

