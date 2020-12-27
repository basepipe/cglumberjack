import stringcase

# meta_data = get_meta_data2(r'Z:\COMPANIES\loneCoconut\render\MABOYA\shots\MBY\0020\comp\hera\000.001\high\.preview\MBY_0020_comp.mp4')
#
# fps = (meta_data['Video Frame Rate'])
# duration_frames = (int(int(meta_data['Video Frame Rate'])*float(meta_data['Duration'].split(' ')[0])))
button_name = 'TestButton'
print(button_name)
print(stringcase.camelcase(button_name))
print(stringcase.titlecase(button_name))
