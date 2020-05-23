from __future__ import print_function
import boto3


def get_upload_link(bucket_name, user):
    return "https://s3.console.aws.amazon.com/s3/buckets/"+bucket_name+"/users/"+user+"/uploads/"


def create_user(bucket_name, user):
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(Bucket=bucket_name, Key="users/testuser/uploads/")
        print(get_upload_link(bucket_name, user))
    except:
        print("whoops")


