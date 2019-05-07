from path import PathObject

filepath = r'D:\cgl-fsutests\source\thedogmovie\shots\000\0000\prev\tmikota\000.000\high\000_0000_prev.mb'

# filepath = r'D:\cgl-fsutests\source\thedogmovie\shots\000\0000\prev\tmikota'

path = PathObject(filepath)

print 'Asset json', path.asset_json
print 'Task json', path.task_json
print 'Proj json', path.project_json
