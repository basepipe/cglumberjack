import os
from cglcore.path import lj_list_dir, PathObject
from cglcore.convert import create_mov, create_hd_proxy

path_object = PathObject(r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectH/shots/SJM/010/comp/tmiko/003.003/high/SJM_010.#######.dpx')
hd_proxy = create_hd_proxy(path_object.path_root)
print hd_proxy
print path_object.preview_path_full
create_mov(hd_proxy, path_object.preview_path_full, thumb_path=path_object.thumb_path_full)
# hd_proxy = r'D:\VFX\FRIDAY_ROOT\cglumberjack\render\cgl_testProjectH\shots\SJM\010\comp\tmiko\003.003\hdProxy'
# print 'Creating Preview Movie at: %s' % shared_data['path_object'].preview_path_full
# create_mov(hd_proxy, output=self.shared_data['path_object'].preview_path_full)