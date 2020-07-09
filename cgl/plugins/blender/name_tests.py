import stringcase
from cgl.core.project import get_cgl_tools, get_cgl_config



text = 'This is a test'

text_ = stringcase.snakecase(text)
print(text_)
menu_name = stringcase.pascalcase(text_)
print(menu_name)
print(stringcase.titlecase(text_))

print(get_cgl_tools())
