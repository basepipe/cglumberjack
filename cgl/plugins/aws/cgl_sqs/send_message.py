import os
import boto3

ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
SECRET_KEY = os.environ['AWS_SECRET_KEY']
region_name = os.environ['AWS_DEFAULT_REGION']

# Create SQS client
sqs = boto3.client('sqs', aws_access_key_id=ACCESS_KEY,
                   aws_secret_access_key=SECRET_KEY,
                   region_name=region_name)

queue_url = 'https://sqs.us-east-1.amazonaws.com/044899505732/CGL_SYNC'

# Send message to SQS queue
response = sqs.send_message(
    QueueUrl=queue_url,
    DelaySeconds=10,
    MessageAttributes={
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
    },
    MessageBody=(
        'Information about current NY Times fiction bestseller for '
        'week of 12/11/2016.'
    )
)

print(response['MessageId'])
