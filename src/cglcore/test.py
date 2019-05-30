import path


test = r'D:/VFX/companies/cgl-fsutests/source/comptestB/shots/SEA/1500/comp/tmikota/000.000/high/SEA_1500_comp.nk'

path_object = path.PathObject(test)


print path_object.path_root
print path_object.company_config