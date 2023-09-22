import os
import boto3
import botocore
import io

def get_file(filename):
    session = boto3.session.Session()
    client = session.client('s3',
                            config=botocore.config.Config(s3={'addressing_style': 'virtual'}),
                            region_name='syd1',
                            endpoint_url='https://syd1.digitaloceanspaces.com',
                            aws_access_key_id=os.getenv('SPACES_KEY'),
                            aws_secret_access_key=os.getenv('SPACES_SECRET'))

    try:
        file = client.get_object(Bucket='catstore', Key=filename)
    except Exception as e:
        return None

    body = file.get("Body")
    bytes = body.read()
    file = io.BytesIO(bytes)
    client.delete_object(Bucket='catstore', Key=filename)
    return file