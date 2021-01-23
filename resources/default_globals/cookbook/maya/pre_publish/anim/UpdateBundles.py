from cgl.plugins.preflight.preflight_check import PreflightCheck
# there is typically a lumbermill.py, and utils.py file in the plugins directory.
# look here for pre-built, useful functions
from cgl.plugins.maya.utils import get_bundles
from cgl.plugins.maya.tasks.bndl import get_latest_publish


class UpdateBundles(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        bundles = get_bundles()
        for each in bundles:
            # check to see what version it is.
            path = pm.getAttr('%s.BundlePath' % each)
            latest = get_latest_publish(path)
            if path != latest:
                print(path)
                print(latest)
                print('path does not equal latest')
        self.pass_check('Updated all bundles')
