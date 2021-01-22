from cgl.core.path import PathObject

company = 'NewCo'
project = 'Branches'



# String Tests
"""
test_path = r'Z:/Projects/NewCo'
test_path = r'Z:/Projects/NewCo/source'
test_path = r'Z:/Projects/NewCo/source/Branches'
test_path = r'Z:/Projects/NewCo/source/Branches/master'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100/anim'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100/anim/default'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100/anim/default/cab18n'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100/anim/default/cab18n/002.000'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100/anim/default/cab18n/002.000/high'
test_path = r'Z:/Projects/NewCo/source/Branches/master/shots/003/0100/anim/default/cab18n/002.000/high/003_0100_anim.mb'
print('Test Path {}'.format(test_path))
path_object = PathObject(test_path)
print('Company {}'.format(path_object.company))
print('Context {}'.format(path_object.context))
print('Project {}'.format(path_object.project))
print('Branch {}'.format(path_object.branch))
print('Scope {}'.format(path_object.scope))
print('Seq {}'.format(path_object.seq))
print('Shot {}'.format(path_object.shot))
print('Variant {}'.format(path_object.variant))
print('User {}'.format(path_object.user))
print('Version {}'.format(path_object.version))
print('Resolution {}'.format(path_object.resolution))
print('filename {}'.format(path_object.filename))
"""

# # dict Tests
# d_ = {"company": company,
#       "context": 'source',
#       "project": project,
#       "scope": 'shots',
#       "seq": '003',
#       "shot": '0100',
#       "task": 'anim',
#       "user": 'cab18n',
#       "version": '002.000',
#       "resolution": 'high',
#       "filename": '003_0100_anim.mb'
#       }

path_ = r'Z:/Projects/cmpa-animation/source/02BTH_2021_Kish/animonly/*'

path_object = PathObject(path_)
print(path_object.path_root)