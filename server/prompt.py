import boto3
import json
import os
from . import aws
from . import conf




_prompt_cache = dict()

# 从 S3 读取 JSON 文件
def read_conf_from_s3(s3_client, bucket, key):
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        # 将字符串解码为 JSON 对象
        json_object = json.loads(file_content)
        return json_object
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get(file_key)->dict:
    if len(_prompt_cache) != 0:
        return _prompt_cache[file_key]

    s3_client = aws.get("s3")

    bucket_name = os.environ['BUCKET_NAME']

    for item in ['EXAMPLE_FILE_NAME', 'PROMPT_FILE_NAME', 'RAG_FILE_NAME']:
        key = os.environ[item]
        json_data = read_conf_from_s3(s3_client, bucket_name, key)
        _prompt_cache[item] =json_data

    return _prompt_cache[file_key]

def template_question(question:str):
    questions = list()
    
    templates = conf.get_sql_templates()
    for key in templates:
        item = templates[key]
        params = item['params']
        questions.append(f"<option><q>{key}</q>该问题的参数是：<params>{params}</params></option>")

    questions_str = "\n".join(questions)
    p = f"""
    备选问题是如下：
    {questions_str}
    请注意*每个备选问题的参数都是占位符，是一种变量，可以被其他相同类型的数据类型替换*
    用户的问题是：<user_questions>{question}</user_questions>
    请严格遵守如下思考方式，思考问题：
    1. 用户的问题，那些是要查询的信息，那些是查询条件
    2. 判断查询信息是否相似：备选问题如果没有直接给出用户问题的查询信息，则说明数据库中不存在用户问题查询的信息，则不相似，否则相似。
    3. 判断查询条件是否相似：用户问题中的查询条件，除了参数不一致，条件的主语和谓词是否都一致，如果一致则判定和备选问题相似，否则不相似
    4. 如果查询信息和查询条件都判定为相似，则判定用户问题和备选问题相似，否则两个问题不相似

    
    请参数下面三个例子：
    <example1>
    备选问题：请查询用户123账号下设备型号是xxx1的设备的数量和总发电量
    用户问题：用户456的，机型是bac的装机容量
    思考：
    1. 用户问题要查询的信息是装机容量，查询条件是 用户账号，设备型号
    2. 由于要查询的装机容量在备选问题中不存在，则查询信息不相似
    结论：用户问题和备选问题不相似
    </example1>
    
    <example2>
    备选问题：请查询用户123账号下机型是xxx1的设备的数量和总发电量
    用户问题：用户aa222机型rttt的发电量
    思考：
    1. 用户问题要查询的信息是发电量，查询条件是 用户账号，设备型号
    2. 由于要查询的发电量在备选问题中极为相似，则判定查询信息相似
    3. 由于用户问题的查询条件和备选问题的查询条件除了参数不同，主语和谓语都相似，则判定查询条件相似
    4. 由于查询信息和查询条件都相似，则用户问题和备选问题相似
    结论：用户问题和备选问题相似
    </example2>

    <example3>
    备选问题：请查询用户123账号下机型是xxx1的设备的数量和总发电量
    用户问题：用户0090的发电量
    思考：
    1. 用户问题要查询的信息是发电量，查询条件是 用户账户
    2. 由于要查询的发电量在备选问题中极为相似，则判定查询信息相似
    3. 由于用户问题的缺少查询条件（机型条件），则判定查询条件不相似
    4. 由于查询条件不相似，则用户问题和备选问题不相似
    结论：用户问题和备选问题不相似
    </example3>

    请根据上述方式思考：在备选问题中找出与用户问题相似的问题并返回用户问题中的参数，以及判断的原因（请按照思考步骤给出原因）,返回格式如下:
    {{
        "question":"您选择的最相似的备选问题",
        "params":["您从用户的问题中找到的参数列表"],
        "reason":"与用户问题问题相似的原因"，
    }}
    如果用户问题和备选问题中不相似，请返回如下格式：
    {{
        "error":"无法找到相似问题",
         "reason":"与用户问题问题不相似的原因"
    }}
    注意：请不要返回其他任何信息
    """
    return p

def template_sql_columns(sql:str,raw_question:str):
 
    p = f"""
    问题:
    {raw_question}对应SQL如下:
    {sql}
    上述sql在数据库中执行后，请分析数据库将返回的数据列,并且根据用户问题和SQL分析这些返回的列是维度还是度量，并以如下格式返回列信息和列对应的维度，度量信息:
    {{
        "columns":["您从sql中发现的需要查询的数据列"],
        "columns_type":["每个列是维度还是度量"]
    }}
    如果sql有语法错误，请返回如下格式的信息：
    {{
        "error":"sql执行错误"
    }}
    注意：请不要返回其他任何信息。
    """
    return p


def template_sql(question:str):
    templates = conf.get_sql_templates()
    if question in templates:
        return templates[question]["content"]

    return ''
    