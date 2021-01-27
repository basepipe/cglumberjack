from cgl.plugins.preflight.preflight_check import PreflightCheck
import pymel.core as pm
# there is typically a lumbermill.py, and utils.py file in the plugins directory.
# look here for pre-built, useful functions
# from cgl.plugins.SOFTWARE import lumbermill


class RemoveDoubleNamespaces(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        children = []
        for each in pm.ls('*:*:mdl'):
            p, c, mdl = each.split(':')
            child = ':%s:%s' % (p, c)
            if child not in children:
                try:
                    pm.namespace(removeNamespace=child, mergeNamespaceWithParent=True)
                    children.append(child)
                except:
                    self.fail_check('Failed to remove namespace: %s' % child)
        self.pass_check('Check Passed, Removed Any Namespaces')
