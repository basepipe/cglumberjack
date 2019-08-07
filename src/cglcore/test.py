from cglcore.path import PathObject

# noinspection SpellCheckingInspection,PyPep8
mov = r'D:/VFX/FRIDAY_ROOT/grindhouse/render/ninjaNunsII/assets/char/trex/ref/tmiko/000.000/high/81zuLQ622hL._SL1500_.jpg'

path_object = PathObject(mov)
print path_object.preview_path_full
print path_object.thumb_path_full

path_object.create_previews()


