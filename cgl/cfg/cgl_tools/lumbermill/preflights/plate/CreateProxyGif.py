from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_gif_proxy, create_gif_thumb


class CreateProxyGif(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # get the sequence to be converted
        from_file = self.shared_data['hdProxy']
        self.shared_data['gifProxy'] = create_gif_proxy(from_file)
        self.shared_data['gifThumb'] = create_gif_thumb(from_file)
        self.pass_check('Finished Creating Gifs!')

