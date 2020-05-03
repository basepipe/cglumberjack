import os
import boto3

# Create SQS client
ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
SECRET_KEY = os.environ['AWS_SECRET_KEY']
region_name = os.environ['AWS_DEFAULT_REGION']

# Create SQS client
sqs = boto3.client('sqs', aws_access_key_id=ACCESS_KEY,
                   aws_secret_access_key=SECRET_KEY,
                   region_name=region_name)

queue_url = 'https://sqs.us-east-1.amazonaws.com/044899505732/CGL_SYNC'

# Receive message from SQS queue
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

message = response['Messages'][0]
receipt_handle = message['ReceiptHandle']
print message
print receipt_handle

# Delete received message from queue
sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=receipt_handle
)
print('Received and deleted message: %s' % message)