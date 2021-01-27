from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_mov


class CreateProxyMov(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        create_mov(self.shared_data['hdProxy'])
        self.pass_check('Movie Created!')
        
        

