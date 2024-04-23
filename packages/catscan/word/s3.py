import os
import boto3
import botocore

def get_client():
    session = boto3.session.Session()
    return session.client('s3',
                            config=botocore.config.Config(s3={'addressing_style': 'virtual'}),
                            region_name='syd1',
                            endpoint_url='https://syd1.digitaloceanspaces.com',
                            aws_access_key_id=os.getenv('SPACES_KEY'),
                            aws_secret_access_key=os.getenv('SPACES_SECRET'))
def get_file(filename):
    client = get_client()
    try:
        file = client.get_object(Bucket='catstore', Key=filename)
        body = file.get("Body")
        return body.read()
    except Exception as e:
        return None

def delete_file(filename):
    client = get_client()
    try:
        client.delete_object(Bucket='catstore', Key=filename)
    except Exception as e:
        return False
    return True

def put_file(filename, file):
    client = get_client()
    try:
        client.put_object(Bucket='catstore', Key=filename, Body=file)
    except Exception as e:
        return False
    return True