import os
import colorsys
import matplotlib.pyplot as plt
from cgl.core.cgl_info import get_cgl_info_size
from cgl.core.utils.general import clean_file_list

# TODO - eventually i want this to behave exactly like daisyDisk.
# i want to always show one layer of folders in the center, all their children on the second ring, and their grandchildren
# on the 3rd ring.  we just have to intercept clicks somehow and it'll tell us what to change root to.

RADIUS = .7
RINGWIDTH = .3
root_path = r'Z:/Projects/VFX/source/16BTH_2020_Arena/assets'


def get_folder_info(root, multiplier=.6, base_color=None, num_folders=None):
    colors = [plt.cm.Blues, plt.cm.Reds, plt.cm.Greens, plt.cm.Blues, plt.cm.Reds,
              plt.cm.Greens, plt.cm.Greens, plt.cm.Blues, plt.cm.Reds, plt.cm.Greens]
    root = root.replace('\\', '/')
    graph_dict = {}
    for parent in clean_file_list(os.listdir(root)):
        folder = os.path.join(root, parent).replace('\\', '/')
        if os.path.isdir(folder):
            graph_dict[parent] = {'size': get_cgl_info_size(folder, source=True, render=True, return_type='bytes'),
                                  'location': folder,
                                  'color': ''
                                  }
    group_names = graph_dict.keys()
    group_sizes = []
    group_colors = []

    for i, g in enumerate(group_names):
        group_sizes.append(graph_dict[g]['size'])
        try:
            group_colors.append(colors[i](multiplier))
        except IndexError:
            group_colors.append(colors[0](multiplier))
    return group_names, group_sizes, group_colors


group_names, group_sizes, group_colors = get_folder_info(root_path)
# Create colors
a, b, c = [plt.cm.Blues, plt.cm.Reds, plt.cm.Greens]
# First Ring (outside)
fig, ax = plt.subplots()
ax.axis('equal')
mypie, _ = ax.pie(group_sizes, radius=RADIUS, labels=group_names, colors=group_colors)
plt.setp(mypie, width=RINGWIDTH, edgecolor='white')

# group_size = [12, 11, 30, 10, 10, 10]
subgroup_names = []
subgroup_sizes = []
subgroup_colors = []
sub_colors = []
for i, f in enumerate(group_names):
    r, g, b, a = group_colors[i]
    h, sat, v = colorsys.rgb_to_hsv(r, g, b)
    path = os.path.join(root_path, f)
    groups, sizes, colors = get_folder_info(path)
    for g in groups:
        subgroup_names.append(g)
    for s in sizes:
        subgroup_sizes.append(s)
    for ci, c in enumerate(colors):
        lenth = float(len(colors))
        multiplier = (ci+1)*(1/lenth)
        rgb = colorsys.hsv_to_rgb(h, abs(sat*multiplier-.2), v)
        r, g, b = rgb
        subgroup_colors.append((r, g, b, 1.0))
# Second Ring (Inside)
mypie2, _ = ax.pie(subgroup_sizes, radius=RADIUS+RINGWIDTH, labels=subgroup_names, labeldistance=0.7,
                   colors=subgroup_colors)
plt.setp(mypie2, width=RINGWIDTH, edgecolor='white')
plt.margins(0, 0)

# show it
plt.show()
