import boto3
import time
import os
import json
import re

from . import aws

def _to_claude_response(streaming_response)->str:
    texts = list()
    for event in streaming_response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk["type"] == "content_block_delta":
            texts.append(chunk["delta"].get("text", ""))
    text = "".join(texts)
    return text
      

def format_bedrock_result(bedrock_res):
    if not bedrock_res:
        return ''

    # 替换换行符并去除首尾空白字符
    bedrock_res = bedrock_res.replace('\n', ' ').strip()

    # 去除字符串开头的三重引号或三重反引号
    if bedrock_res.startswith(('"""', "'''")):
        bedrock_res = bedrock_res[3:]

    # 去除字符串开头的 "json"
    if bedrock_res.startswith('json'):
        bedrock_res = bedrock_res[4:]

    # 去除字符串末尾的三重引号或三重反引号
    if bedrock_res.endswith(('"""', "'''")):
        bedrock_res = bedrock_res[:-3]

    # 替换三重引号内的引号
    while True:
        match = re.search(r'"""(.*?)"""', bedrock_res)
        if not match:
            break
        change_item = match.group(1)
        change_item = change_item.replace('"', '\\"')
        bedrock_res = bedrock_res[:match.start()] + change_item + bedrock_res[match.end():]

    # 替换多余的空白字符和去除三重单引号
    bedrock_res = re.sub(r'\s+', ' ', bedrock_res).replace("'''", '')

    # 替换三重引号为双引号
    bedrock_res = bedrock_res.replace('"""', '"')

    return bedrock_res


def _query_embedding(questions:list, bedrock_client=None):
    embedding_model_id = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-image-v1')

    if not bedrock_client:
        bedrock_client = aws.get('bedrock-runtime')

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages":questions

    }
    # Convert the native request to JSON.
    request = json.dumps(native_request)

    response = bedrock_client.invoke_model_with_response_stream(
        body=request,
        contentType='application/json',
        accept='*/*',
        modelId=embedding_model_id,
    )

    text = _to_claude_response(response)
    return text

def query(questions:list, bedrock_client=None):
    if not bedrock_client:
        bedrock_client = aws.get('bedrock-runtime')

    model_id = os.environ.get('MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 20480,
        "temperature": 0,
        "top_p":1,
        "top_k":1,
        "messages":questions
    }
    # Convert the native request to JSON.
    request = json.dumps(native_request)
    try_times = 0
    while try_times < 3:
        try:
            response = bedrock_client.invoke_model_with_response_stream(
                body=request,
                contentType='application/json',
                accept='*/*',
                modelId=model_id,
            )

            text = _to_claude_response(response)
            return text

        except Exception as ex:
            time.sleep(3)
            try_times +=1
    return ""







