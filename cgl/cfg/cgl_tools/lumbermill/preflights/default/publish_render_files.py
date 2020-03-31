import os
from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.path import PathObject
from cgl.core.utils.general import cgl_copy


# noinspection PyPep8Naming
class publish_render_files(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        path_object = self.shared_data['path_object']
        user = path_object.user
        if path_object.context != 'render':
            path_object = PathObject.copy(path_object, context='render')
        from_dir = os.path.dirname(path_object.path_root)
        pub_obj = PathObject(from_dir)
        pub_obj = pub_obj.copy(latest=True)
        pub_obj.set_attr(user='publish')
        pub_obj = pub_obj.next_major_version()
        major_version_obj = pub_obj.copy(user=user)
        for each in os.listdir(from_dir):
            print(os.path.join(from_dir, each), os.path.join(major_version_obj.path_root, each))
            print(os.path.join(from_dir, each), os.path.join(pub_obj.path_root, each))
            cgl_copy(os.path.join(from_dir, each), os.path.join(major_version_obj.path_root, each))
            cgl_copy(os.path.join(from_dir, each), os.path.join(pub_obj.path_root, each))
        self.pass_check('Done Copying Render Files to %s' % pub_obj.path_root)

