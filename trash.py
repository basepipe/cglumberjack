from cgl.core.metadata import get_meta_data2

meta_data = get_meta_data2(r'Z:\COMPANIES\loneCoconut\render\MABOYA\shots\MBY\0020\comp\hera\000.001\high\.preview\MBY_0020_comp.mp4')

fps = (meta_data['Video Frame Rate'])
duration_frames = (int(int(meta_data['Video Frame Rate'])*float(meta_data['Duration'].split(' ')[0])))