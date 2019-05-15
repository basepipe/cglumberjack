import os

test = r'D:\cgl-fsutests\render\test5\shots\020\0800\lite\publish\000.000\high'

print os.path.splitext(test)
if os.path.splitext(test)[-1]:
    print 'this is a file'
    dir_ = os.path.dirname(test)
else:
    dir_ = test

print dir_