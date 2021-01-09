import requests
import os
import logging
from cgl.core.config.config import ProjectConfig


def slack_notification_email(type_='reviews', subject='Generic Subject', message='This is a message',
                             attachments=None, cfg=None):
    if not cfg:
        cfg = ProjectConfig()
    email = cfg.project_config['email']
    from_name = ''
    if type_ == 'bugs':
        from_name = 'Lumbermill Bugs'
    elif type_ == 'reviews':
        from_name = 'Review Requested'
    files_ = None
    if attachments:
        files_ = {}
        count = 0
        for a in attachments:
            with open(a, 'rb') as f:
                files_['attachment['+str(count)+']'] = (os.path.basename(a), f.read())
            count += 1
    logging.info('sending email...')
    return requests.post(email['lj_domain'],
                         auth=("api", email['mailgun_key']),
                         files=files_,
                         data={"from": "%s <%s>" % (from_name, email['from']),
                               "to": [email[type_]],
                               "subject": subject, "text": message},
                         )
