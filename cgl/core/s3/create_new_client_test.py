from core.s3.s3_directory import send_mail

client = 'tofu'
user = 'joey'
#email = 'synthure@gmail.com'
email = '12975439@qq.com'

# we should set this up so that it is smart enough to check if the bucket exists and create it if needed
# we should set this up so that it is smart enough to check if the user exists and create it if needed

send_mail(email, user, bucket_name=client, new_bucket=True, new_user=True)


