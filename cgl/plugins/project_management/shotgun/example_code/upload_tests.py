from plugins.project_management.shotgun.tracking_internal.shotgun_specific import ShotgunQuery
from cgl.core.config import app_config
from cgl.core.path import PathObject

CONFIG = app_config()
SG_CONFIG = app_config()['project_management']['shotgun']['api']
PROJECTSHORTNAME = CONFIG['project_management']['shotgun']['api']['project_short_name']
PROJECTFIELDS = ['code', 'name', 'sg_status', 'sg_description', PROJECTSHORTNAME]
HUMANUSERFIELDS = ['code', 'name', 'email', 'department', 'login']
TASKFIELDS = ['content', 'sg_status_list', 'step', 'step.Step.short_name',
              'project.Project.%s' % PROJECTSHORTNAME, 'task_assignees', 'task_assignees.Humanuser.username',
              'name', 'code', 'project', 'project.Project.sg_status', 'project.Project.status',
              'entity', 'entity.Shot.sg_sequence', 'due_date', 'updated_at', 'entity.Asset.sg_asset_type', 'updated_at']
ASSETFIELDS = ['code', 'name', 'status', 'updated_at', 'description']
SHOTFIELDS = ['code', 'sg_sequence', 'status', 'updated_at', 'description']
VERSIONFIELDS = ['code', 'name', 'sg_sequence', 'status', 'updated_at', 'description',
                 'sg_task', 'sg_status_list', 'project', 'versions']
STEPFIELDS = ['code', 'short_name', 'id', ]

path_ = r'Z:/Projects/VFX/render/16BTH_2020_Arena/assets/Environment/Tongs/shd/tmikota/000.002/high/010_0500_comp.mp4'.replace('/', '\\')
exr_path = r'Z:\Projects\VFX\render\16BTH_2020_Arena\assets\Environment\Tongs\shd\tmikota\000.002\high\010_0500_comp.####.exr'
path_object = PathObject(exr_path)
#print path_object.preview_path
# path_object.make_proxy()
#path_object.make_preview()
id_ = 13759
filters = [['id', 'is', id_],
          ]
version = ShotgunQuery.find_one('Version', filters, fields=VERSIONFIELDS)
print version
#version = find_version_info_from_path(full_path)
id_ = str(version['id'])
print id_, type(id_)
print path_, type(path_)
ShotgunQuery.upload("Version", id_, path_object.preview_path, "sg_uploaded_movie")
#ShotgunQuery.upload('Version', id_, path_object.preview_path, "sg_uploaded_movie")

