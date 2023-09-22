import datetime
import os
import boto3
import botocore

def expire_all():
    session = boto3.session.Session()
    client = session.client('s3',
                            config=botocore.config.Config(s3={'addressing_style': 'virtual'}),
                            region_name='syd1',
                            endpoint_url='https://syd1.digitaloceanspaces.com',
                            aws_access_key_id=os.getenv('SPACES_KEY'),
                            aws_secret_access_key=os.getenv('SPACES_SECRET'))

    count = 0
    current_time = datetime.datetime.now()
    objects = client.list_objects(Bucket='catstore')
    if 'Contents' in objects:
        for obj in objects['Contents']:
            last_modified = obj['LastModified']
            time_difference = (current_time - last_modified).total_seconds() / 60
            if time_difference > 5:
                client.delete_object(Bucket='catstore', Key=obj['Key'])
                count = count + 1

    return count

def main():
    return {'body': expire_all()}