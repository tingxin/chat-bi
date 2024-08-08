import boto3
import json
import os
from . import aws


_prompt_cache = dict()

# 从 S3 读取 JSON 文件
def read_json_from_s3(s3_client, bucket, key):
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        # 将字符串解码为 JSON 对象
        json_object = json.loads(file_content)
        return json_object
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get(file_key):
    if len(_prompt_cache) != 0:
        return _prompt_cache[file_key]

    s3_client = aws.get("s3")

    bucket_name = os.environ['BUCKET_NAME']

    # EXAMPLE_FILE_NAME=sungrow/defaultDragonPrompt.json
    # PROMPT_FILE_NAME=sungrow/promptConfig.json
    # RAG_FILE_NAME=sungrow/ragSampleList.json
    

    for item in ['EXAMPLE_FILE_NAME', 'PROMPT_FILE_NAME', 'RAG_FILE_NAME']:
        key = os.environ[item]
        json_data = read_json_from_s3(s3_client, bucket_name, key)
        _prompt_cache[item] =json_data

    return _prompt_cache[file_key]