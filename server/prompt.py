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
        questions.append(f"<option><q>{key}</q>该问题的参数是：<params>{params}</params>，参数都是不固定的，可变的</option>")

    questions_str = "\n".join(questions)
    p = f"""
    备选问题是如下：
    {questions_str}
    请注意*每个备选问题的参数都是占位符，是一种变量，可以被其他相同类型的数据类型替换*
    用户的问题是：<user_questions>{question}</user_questions>

    对每一个备选问题,请与用户问题进行对比，严格遵守如下思考方式，进行判定：
    1. 用户的问题中那些是要查询的信息,那些是查询条件，查询条件的个数 user_condition_count
    2. 备选问题中那些是要查询的信息，那些查询条件，查询条件的个数 option_condition_count
    3. 创建变量result, 令 result = user_condition_count == option_condition_count 
    4. (if result == True继续思考，否则直接到第六步)判定查询条件，如果查询条件主语和谓语都相同，result = result && True，否则 result = result && False
    5. (if result == True继续思考，否则直接到第六步)判断查询信息是否相似：备选问题如果没有直接给出用户问题的查询信息，则说明数据库中不存在用户问题查询的信息 result = result & False。
    6. 检查 result 的值
    如果 result == True 则按如下格式返回 并停止思考:
    {{
        "question":"当前的备选问题",
        "params":["您从用户的问题中，参考备选问题及它的参数列表，找到的查询参数列表"],
        "reason":"按上述思考步骤得出result == True的原因，把每一个步骤的result的值和原因都要写明",
        "result: result 的值
    }}
    如果 result == False, 则继续把下一个备选问题 与用户问题 按上述步骤处理。

    如果对所有备选问题和用户问题思考后，没有任何一个备选问题与用户问题，经过上述思考得出 result == False，则返回格式如下:
    {{
        "error":"未能找到匹配的问题",
        "reason":"得出result == True的原因",
        "result: result 的值
    }}
   
    **注意：请不要返回其他任何信息**

    请严格参考下面三个例子：
    <example1>
    备选问题：请查询用户123账号下设备型号是xxx1的设备的数量和总发电量
    用户问题：用户456的，机型是bac的装机容量
    思考：
    1. 用户问题要查询的信息是装机容量，查询条件是 用户账号，备型号， user_condition_count = 2
    2. 备选问题要查询的信息是设备数量，总发电量，查询条件是 用户账号，设备型号， option_condition_count =  2
    3. result = user_condition_count == option_condition_count
    4. 因为 result == True, 所以执行第四步骤，因为两个问题的查询条件主语和谓语都相似，所以 result = result && True
    5. 因为 result == True, 用户问题的查询信息在备选问题中不存在，则查询信息不相似,所以 所以 result = result && False
    6. result 值为 False， 因为 result == False 所以思考下一个问题
    </example1>
    
    <example2>
    备选问题：请查询用户123账号下机型是xxx1的设备的数量和总发电量
    用户问题：用户222机型rttt的发电量
    思考：
    1. 用户问题中查询的信息是发电量，查询条件是 用户账号，设备型号， user_condition_count = 2
    2. 备选问题中查询的信息是设备数量，总发电量，查询条件是 用户账号，option_condition_count =  2
    3. result = user_condition_count == option_condition_count
    4. 因为 result == True, 所以执行第四步骤,由于用户问题的查询条件和备选问题的查询条件除了参数不同，主语和谓语都一致，则result = result && True
    5. 因为 result == True,由于要查询的发电量在备选问题中极为相似，则则result = result && True
    6. result = True，因为result == True
    返回{{
        "question":"请查询用户123账号下机型是xxx1的设备的数量和总发电量",
        "params":[222，"rttt"],
        "reason":"得出result == True的原因",
        "result: result 的值
    }}
    </example2>

    <example3>
    备选问题：请查询用户123账号下机型是xxx1的设备的数量和总发电量
    用户问题：用户0090的发电量
    思考：
    1. 用户问题查询的信息是发电量，查询条件是 用户账户 查询条件个数为 user_condition_count =  1
    1. 备选问题查询的信息是设备数量和发电量，查询条件是 用户账户和机型 option_condition_count =  2
    2. 由于要查询的发电量在备选问题中极为相似，则判定查询信息相似
    3. result = user_condition_count ==option_condition_count
    4. 因为 result == False, 直接到第六步
    6. result = False,  因为 result == False 所以思考下一个问题
    </example3>


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
    