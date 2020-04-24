import os
import boto3
import click
import time
import cgl.plugins.syncthing.utils as st_utils

try:
    ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
    SECRET_KEY = os.environ['AWS_SECRET_KEY']
    REGION_NAME = os.environ['AWS_DEFAULT_REGION']
except KeyError:
    print 'ERROR: You need to define the following env variables: ACCESS_KEY, SECRET_KEY, REGION_NAME'

test_message_body = 'Information about current NY Times fiction bestseller for week of 12/11/2016.'
test_message_attrs = {
                        'Title': {
                            'DataType': 'String',
                            'StringValue': 'The Whistler'
                        },
                        'Author': {
                            'DataType': 'String',
                            'StringValue': 'John Grisham'
                        },
                        'WeeksOn': {
                            'DataType': 'Number',
                            'StringValue': '6'
                        }
                     }


def send_message(message_attrs=test_message_attrs, message_body=test_message_body):
    sqs = boto3.client('sqs', aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_KEY,
                       region_name=REGION_NAME)
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
    sqs = boto3.client('sqs', aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_KEY,
                       region_name=REGION_NAME)
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
    print '-->>: Recieved %s new events' % len(response['Messages'])
    if 'Messages' in response.keys():
        messages = response['Messages']
        return messages, sqs, queue_url
    else:
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
    sqs = boto3.client('sqs', aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_KEY,
                       region_name=REGION_NAME)

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
                    print 'CGL Event Found: "Machine Added"'
                    do_delete = add_machine_to_syncthing(message['MessageAttributes'], test=test)
                elif message['MessageAttributes']['message_type']['StringValue'] == 'Folders Shared':
                    print 'CGL Event Found: "Folders Shared"'
                    do_delete = accept_folders_from_syncthing(message['MessageAttributes'], test=test)
                else:
                    print 'Unexpected Event: %s' % message['MessageAttributes']['message_type']['StringValue']
            if do_delete or force_delete:
                print '\t -->> processing complete, deleting message'
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
            else:
                print '\t -->> message not processed, skipping delete'
    else:
        print 'CGL Events: No Events To Process'


def add_machine_to_syncthing(message_attrs, test=True):
    try:
        device_id = message_attrs['device_id']['StringValue']
        name = message_attrs['device_name']['StringValue']
        print '\t -->> Adding device %s:%s to syncthing' % (device_id, name)
        if not test:
            st_utils.kill_syncthing()
            print('adding %s to sync' % name)
            st_utils.add_device_to_config(device_id=device_id, name=name)
            st_utils.launch_syncthing()
            st_utils.kill_syncthing()
            print('sharing files to %s' % name)
            st_utils.share_files_to_devices(all_device_id=[device_id])
            print 'Sending Folders Shared Message'
            folders_shared_message(device_id=device_id, device_name=name,
                                   message='Shared Files with %s, check config')
            st_utils.launch_syncthing()
            return True
    except KeyError:
        print '\t -->> Did not find expected key in messageAttrs %s, skipping add machine to syncthing' % message_attrs
        return False


def accept_folders_from_syncthing(message_attrs, test=True):
    try:
        device_dict = st_utils.get_my_device_info()
    except:
        print '\t -->> No Device ID Found, cannot accept folders.'
        return
    local_device_id = device_dict['id']
    device_id = message_attrs['device_id']['StringValue']
    if local_device_id == device_id or device_id == 'all':
        print '\t -->> Found New Folders for %s' % device_dict['name']
        if not test:
            st_utils.accept_folders()  # this has kill and launch syncthing built in.
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
    start_time = time.time()
    while True:
        process_messages(force_delete=delete)
        time.sleep(seconds - ((time.time() - start_time) % seconds))


if __name__ == "__main__":
    main()



