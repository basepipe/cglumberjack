from cglcore.config import app_config
import ftrack_api
import datetime


def setup():
    """
    Function to collect info from config file to setup Ftrack query object

    NOTE: Function causes a delay in the time tracker gui

    :return: Query Session object
    """
    # TODO Figure out the delay when using this function in lumbermill
    server_url = app_config()['project_management']['ftrack']['api']['server_url']
    api_key = app_config()['project_management']['ftrack']['api']['api_key']
    api_user = app_config()['project_management']['ftrack']['api']['api_user']

    ftrack = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)
    return ftrack


def get_all_projects():
    """
    Function to get a list of all projects for a company in ftrack

    :return: Returns a list of Project Objects
    """
    ftrack = setup()
    proj_list = []
    proj = ftrack.query("Project")
    for p in proj:
        proj_list.insert(0, p['name'])
    return proj_list


def get_user(email_address='lonecoconutmail@gmail.com'):
    """
    Function to get user object from ftrack
    :param email_address: FTrack user's email address
    :type email_address: String
    :return: Ftrack User Object
    """
    ftrack = setup()
    return ftrack.query('User where username is "{}"'.format(email_address)).first()


def get_timelogs(month=datetime.datetime.today().month, day=datetime.datetime.today().day, year=datetime.datetime.today().year):
    """
    Function to get all timelog objects for a certain date
    :return: List of timelog objects
    """
    ftrack = setup()
    date1 = datetime.datetime(year, month, day)
    date2 = date1 + datetime.timedelta(days=1)
    date1 = date1.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    date2 = date2.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    timelogs = []
    logs = ftrack.query("Timelog where start >= '%s' and start <= '%s'" % (date1, date2))
    for log in logs:
        timelogs.append(log)
    return timelogs


def edit_timelog(task_name, hours):
    ftrack = setup()
    hours = float(hours)
    hours = hours * 60 * 60
    task = ftrack.query("Task where name is '%s'" % task_name)
    print task_name
    task_id = task[0]['id']
    print task_id
    timelog = ftrack.query("Timelog where context_id is '%s'" % task_id)
    print timelog
    for t in timelog:
        print t
    timelog[0]['duration'] = float(hours)
    ftrack.commit()

def create_timelog(task, hours, month, day, year):
    """
    Function to create a new timelog and send it to ftrack
    :param task: Task to add timelog to
    :type task: Ftrack Task Object
    :param hours: Hours to add to timelog
    :type hours: Float
    :return: None
    """
    ftrack = setup()
    user_id = get_user()['id']
    task_id = task['id']
    seconds = hours*60*60
    date1 = datetime.datetime(year, month, day)
    date1 = date1.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    new_log = ftrack.create('Timelog', {"user_id": user_id, "duration": seconds, "start": date1, "context_id": task_id})
    task['timelogs'].append(new_log)
    ftrack.commit()


def get_all_tasks(proj_name):
    """
    Function to get a list of all tasks for a project in ftrack

    :param proj_name: Name of Project to get info from
    :type proj_name: String
    :return: List of Task Objects
    """
    ftrack = setup()
    task_list = []
    t = ftrack.query("Task where project.name is '%s'" % proj_name)
    for task in t:
        task_list.insert(0, task)
    return task_list


if __name__ == '__main__':
    t = get_all_tasks('cgl_testProjectA')
    test = get_timelogs(datetime.datetime.today().month, datetime.datetime.today().day, datetime.datetime.today().year)
