import os
import boto3
import click
import time
import cgl.plugins.syncthing.utils as st_utils


def check_st_config(folder_type='sendreceive'):
    import cgl.apps.lumber_watch.lumber_watch as lw
    if st_utils.syncthing_synced():
        # print('Nothing to Sync')
        if lw.check_syncthing_config():
            print('Detected Changes in Config - Syncing Lumbermill')
            st_utils.kill_syncthing()  # do i have to kill it to process pending folders and devices?
            print('Processing syncthing config')
            st_utils.process_pending_devices()
            st_utils.process_pending_folders(folder_type=folder_type)
            st_utils.process_folder_naming()
            st_utils.launch_syncthing()


def send_message(message_attrs='', message_body=''):
    sqs = boto3.client('sqs')
    # TODO - put this in the globals
    queue_url = 'https://sqs.us-east-1.amazonaws.com/044899505732/CGL_SYNC'
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes=message_attrs,
        MessageBody=message_body
    )
    print(response['MessageId'])


def receive_messages(queue_url='https://sqs.us-east-1.amazonaws.com/044899505732/CGL_SYNC'):
    sqs = boto3.client('sqs')
    # TODO - put this in the globals

    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=10,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    if 'Messages' in response.keys():
        print('Lumberwatch:  %s New Events' % len(response['Messages']))
        messages = response['Messages']
        return messages, sqs, queue_url
    else:
        print('Lumberwatch: No New Messages')
        return None, None, None


def process_messages(max_messages=1,
                     queue_url='https://sqs.us-east-1.amazonaws.com/044899505732/CGL_SYNC',
                     test=False, force_delete=False):
    """

    :param max_messages:
    :param queue_url:
    :param test:
    :param force_delete:
    :return:
    """
    sqs = boto3.client('sqs')

    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=max_messages,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    if 'Messages' in response.keys():
        messages = response['Messages']

        for i, message in enumerate(messages):
            do_delete = False
            receipt_handle = message['ReceiptHandle']
            if 'message_type' in message['MessageAttributes'].keys():
                if message['MessageAttributes']['message_type']['StringValue'] == 'Machine Added':
                    print('CGL Event Found: "Machine Added"')
                    do_delete = add_machine_to_syncthing(message['MessageAttributes'], test=test)
                elif message['MessageAttributes']['message_type']['StringValue'] == 'Folders Shared':
                    pass
                    # print('CGL Event Found: "Folders Shared"')
                    # do_delete = accept_folders_from_syncthing(message['MessageAttributes'], test=test)
                else:
                    print('Unexpected Event: %s' % message['MessageAttributes']['message_type']['StringValue'])
            if do_delete or force_delete:
                print('\t -->> processing complete, deleting message')
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
            else:
                pass
    else:
        print('CGL Events: No Events To Process')


def add_machine_to_syncthing(message_attrs, test=True):
    print('add_machine_to_syncthing')
    try:
        device_dict = st_utils.get_my_device_info()
    except:
        print('\t -->> No Device ID Found, cannot accept folders.')
        return
    local_device_id = device_dict['id']
    try:
        device_id = message_attrs['device_id']['StringValue']
        name = message_attrs['device_name']['StringValue']
        print('\t -->> Adding device %s:%s to syncthing' % (device_id, name))
        if not test:
            st_utils.kill_syncthing()
            print('adding %s to sync' % name)
            st_utils.add_device_to_config(device_id=device_id, name=name)
            st_utils.launch_syncthing()
            st_utils.kill_syncthing()
            print('sharing files to %s' % name)
            st_utils.share_folders_to_devices(device_ids=[device_id], dialog=False)
            print('Sending Folders Shared Message')
            folders_shared_message(device_id=device_id, device_name=name,
                                   message='Shared Files with %s, check config')
            st_utils.launch_syncthing()
            return True
        if local_device_id != device_id:
            print('\t -->> Adding device %s:%s to syncthing' % (device_id, name))
            if not test:
                try:
                    st_utils.kill_syncthing()
                    st_utils.add_device_to_config(device_id=device_id, name=name)
                    st_utils.launch_syncthing()
                    return True
                except:
                    print('\t -->> Failed Adding Machine to Syncthing')
                    return False
        else:
            print('\t -->> Skipping message that originated from this machine.')
    except KeyError:
        print('\t -->> Did not find expected key in messageAttrs %s, skipping add machine to syncthing' % message_attrs)
        return False


def accept_folders_from_syncthing(message_attrs, test=True):
    try:
        device_dict = st_utils.get_my_device_info()
    except:
        print('\t -->> No Device ID Found, cannot accept folders.')
        return
    local_device_id = device_dict['id']
    device_id = message_attrs['device_id']['StringValue']
    # i have to know that this computer is meant to have these folders.
    if local_device_id == device_id:
        print('\t -->> Found New Folders for %s' % device_dict['name'])
        if not test:
            st_utils.process_st_config()  # this has kill and launch syncthing built in.
        return True
    
    
def send_sync_message(device_id, device_name, message, message_type, **kwargs):
    """
    
    :param device_id: 
    :param device_name: 
    :param message_type: 
    :param message: 
    :param kwargs: 
    :return: 
    """
    print("Notifying Lumbermill of New Machine Add")
    message_types = ['Folders Shared', 'Machine Added']
    if message_type in message_types:
        message_attrs = {'device_id': {'DataType': 'String', 'StringValue': device_id},
                         'device_name': {'DataType': 'String', 'StringValue': device_name},
                         'message_type': {'DataType': 'String', 'StringValue': message_type}
                         }
        message_body = message
        for k in kwargs:
            message_attrs[k] = {'DataType': 'String', 'StringValue': kwargs[k]}
        message_body = message
        send_message(message_attrs, message_body)
    

def folders_shared_message(device_id, device_name, message, **kwargs):
    """
    Message sent when folders are shared with a device.
    :param device_id: 
    :param device_name: 
    :param username: 
    :param message: 
    :param message_type: 
    :param kwargs: 
    :return: 
    """
    send_sync_message(device_id=device_id, device_name=device_name, message_type='Folders Shared',
                      message=message, **kwargs)


def machine_added_message(device_id, device_name, message, **kwargs):
    """
    pipeline: sync_thing
    pipeline_id: 206
    :return:
    """
    send_sync_message(device_id=device_id, device_name=device_name, message_type='Machine Added',
                      message=message, **kwargs)


@click.command()
@click.option('--seconds', '-s', default=60.0,
              help='Input the time between running designated lumber watch scripts')
@click.option('--delete', '-d', default=False,
              help='Forces Deletion of messages no matter what.  Useful in testing.')
def main(seconds, delete):
    my_device = st_utils.get_my_device_info()['name']
    devices = st_utils.get_all_devices_from_config()
    if devices:
        print("Connected to:")
        for m in st_utils.get_all_devices_from_config():
            if my_device != m:
                print("\t{} @ {}".format('user_name', m))
    else:
        print('Not currently connected to any devices for syncing')
    print("Ready to Sync.")
    start_time = time.time()
    while True:
        process_messages(force_delete=delete)
        if st_utils.syncthing_running():
            check_st_config()
            time.sleep(5)
        # st_utils.save_all_sync_events()
        time.sleep(seconds - ((time.time() - start_time) % seconds))


if __name__ == "__main__":
    main()



