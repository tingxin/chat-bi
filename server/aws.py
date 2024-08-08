import boto3
import os

def get(service_name:str):
    is_dev =bool(os.getenv('DEV_MODEL'))
    if service_name == 's3' and is_dev:
        client = boto3.client(
            service_name,
            region_name = os.getenv('DEFAULT_REGION')
        )
        return client
           

    if 'ACCESS_KEY' in os.environ and 'SECRET_ACCESS_KEY' in os.environ and len(os.environ['ACCESS_KEY']) == 20:
       return boto3.client(
            service_name,
            region_name = os.getenv('DEFAULT_REGION'),
            aws_access_key_id=os.getenv('ACCESS_KEY'),
            aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY')
       )

    return boto3.client(
            service_name,
            region_name = os.getenv('DEFAULT_REGION')
        )