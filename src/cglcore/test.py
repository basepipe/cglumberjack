import path
from cglcore.convert import create_proxy, create_hd_proxy, create_gif_proxy, create_mov_hd_proxy

test = r'D:/VFX/companies/cgl-fsutests/source/ingest_Test/shots/SEA/0160/comp/tmikota/000.000/high/SEA_0160_comp.nk'


this = path.PathObject(test)

'%s/*' % this.split_after('shot')