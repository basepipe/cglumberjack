import os
import boto3

ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
SECRET_KEY = os.environ['AWS_SECRET_KEY']
REGION_NAME = os.environ['AWS_DEFAULT_REGION']

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
        MessageBody=(message_body)
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
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    if 'Messages' in response.keys():
        print 'yup'
        messages = response['Messages']
        return messages, sqs, queue_url
    else:
        return None, None, None


def delete_message(message, sqs=None, queue_url='https://sqs.us-east-1.amazonaws.com/044899505732/CGL_SYNC'):
    if not sqs:
        sqs = boto3.client('sqs', aws_access_key_id=ACCESS_KEY,
                           aws_secret_access_key=SECRET_KEY,
                           region_name=REGION_NAME)
    receipt_handle = message['ReceiptHandle']
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )


def process_messages(messages, sqs, queue_url, test=False, delete=False):
    """
    Example of how to
    :param messages:
    :return:
    """
    for message in messages:
        print 1
        if 'message_type' in message['MessageAttributes'].keys():
            if message['MessageAttributes']['message_type']['StringValue'] == 'Machine Added':
                print 'Found Machine Added Message'
                success = add_machine_to_syncthing(message['MessageAttributes'], test=test)
            elif message['MessageAttributes']['message_type']['StringValue'] == 'Folders Shared':
                print 'Found Folders Shared Message'
                success = accept_folders_from_syncthing(message['MessageAttributes'], test=test)
            else:
                print 'Found Unexpected message %s' % message['MessageAttributes']['message_type']['StringValue']
        if delete:
            print 'processing complete, deleting message'
            delete_message(message, sqs, queue_url)


def add_machine_to_syncthing(message_attrs, test=True):
    for k in message_attrs:
        print k, message_attrs[k]['StringValue']
    try:
        device_id = message_attrs['device_id']['StringValue']
        name = message_attrs['device_name']['StringValue']
        print 'Adding device %s:%s to syncthing' % (device_id, name)
        if not test:
            import plugins.syncthing.utils as st_utils
            st_utils.kill_syncthing()
            st_utils.add_device_to_config(device_id=device_id, name=name)
            st_utils.launch_syncthing()
        return True
    except KeyError:
        print 'Did not find expected key in messageAttrs %s, skipping add machine to syncthing' % message_attrs
        return False


def accept_folders_from_syncthing(message_attrs, test=True):
    import plugins.syncthing.utils as st_utils
    try:
        device_dict = st_utils.get_my_device_info()
    except:
        print 'No Device ID Found, cannot accept folders.'
        return
    local_device_id = device_dict['id']
    device_id = message_attrs['device_id']['StringValue']
    if local_device_id == device_id or device_id == 'all':
        print 'Found New Folders for %s' % device_dict['name']
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


if __name__ == "__main__":
    # print 'adding new machine to queue'
    # folders_shared_message('23515616', 'bob_machine', 'adding folders for bob')

    # machine_added_message('1515262', 'machine_name', 'hey sucka, you added a machine',
    #                       username='tmikota',
    #                       ftrack_user='tmikota@gmail.com',
    #                       first='Tom',
    #                       last='Mikota',
    #                       phone='850-841-0151')
    messages, sqs, queue_url = receive_messages()
    if messages:
        process_messages(messages, sqs, queue_url, delete=False)
    else:
        print 'No Messages to Process'



