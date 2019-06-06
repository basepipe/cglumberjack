import path
from cglcore.convert import create_proxy, create_hd_proxy, create_gif_proxy, create_mov, get_start_frame


test = r'D:/VFX/companies/cglumberjack/render/ninjaNunsII/shots/010/0100/comp/tmikota/000.000/high/010_0100_comp.%06d.dpx'
#test = r'D:/VFX/companies/cglumberjack/render/ninjaNunsII/shots/010/0100/comp/tmikota/000.000/high/010_0100_comp.######.dpx'
#test = r'D:/VFX/companies/cglumberjack/render/ninjaNunsII/shots/010/0100/comp/tmikota/000.000/high/010_0100_comp.*.dpx'

this = create_mov(test)
# print path.get_start_frame(test)
#print path.prep_seq_delimiter(test, replace_with='#')
#print path.prep_seq_delimiter(test, replace_with='%')

#input_file = path.replace_seq(test)
#output_file = '%s.mov' % input_file.split('.*')[0]

#print input_file
#print output_file