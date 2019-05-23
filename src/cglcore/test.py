from path import PathObject

filepath = r'D:\cgl-fsutests\source\comptest\*'

# filepath = r'D:\cgl-fsutests\source\thedogmovie\shots\000\0000\prev\tmikota'

path = PathObject(filepath)

print path.path_root
