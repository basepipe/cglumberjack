from cgl.core.metadata import get_meta_data2
from cgl.core.path import PathObject

# meta_data = get_meta_data2(r'Z:\COMPANIES\loneCoconut\render\MABOYA\shots\MBY\0020\comp\hera\000.001\high\.preview\MBY_0020_comp.mp4')
#
# fps = (meta_data['Video Frame Rate'])
# duration_frames = (int(int(meta_data['Video Frame Rate'])*float(meta_data['Duration'].split(' ')[0])))

path_object = PathObject(r'Z:/COMPANIES/loneCoconut/render/MABOYA/shots/MBY/0040/plate/publish/000.000/high/MBY_0040_########.exr')
print(path_object.path_root)
print(path_object.frame_range)
