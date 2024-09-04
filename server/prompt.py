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
        questions.append({
            "question":key,
            "params":params
        })

    p = f"""
    备选问题信息集合是如下：
    {questions}
    请注意*每个备选问题包括问题及参数,每个备选问题的参数都是占位符，是一种变量，可以被其他相同类型的数据类型替换*
    用户的问题是：<user_questions>{question}</user_questions>

    请按如下伪代码思考问题：

    分析出用户的问题中那些是要查询信息集合 query_lst, 查询条件集合 query_conditions
    for option_question(备选问题) in questions(备选问题集合):
        对option_question分析出查询信息集合 option_query_lst, option_query_conditions
        if len(query_conditions) != len(option_query_conditions):
            continue
        if 对于用户问题的每一个查询条件，当前备选问题的查询条件中，没有任何一个条件的主语和谓语和用户问题的查询条件主语谓语相同(参数可以不同)：
            continue

        # 将列表转换为集合
        query_set = set(query_lst)
        option_set = set(option_query_lst)

        is_subset = query_set.issubset(option_set)
        if not is_subset:
            continue
            
        return  {{
        "question":option_question,
        "params":["您从用户的问题中，参考备选问题及它的参数列表，找到的查询参数列表"],
        "reason":"思考问题的过程及解释",
        "result: True
        }}

    return  {{
        "error":"未能找到匹配的问题",
        "reason":"",
        "result: False
    }}
    *请不要做任何解释，直接返回return 语句后面的对象，并且保证return 后面的对象能够被转成json对象*
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

def template_fix_query_error(error:str)->str:
    t = f"""根据前面讨论，你返回了SQL, 但是，{error}, 请根据错误信息，修改SQL，按如下格式返回，并保证返回的格式能够被转成json 对象，不要做任何解释。返回格式:
    {{
    "finalSQL":"修正后的sql",
    "reason":"解释为什么这么修改"
    }}
    """
    return t

def template_sql(question:str):
    templates = conf.get_sql_templates()
    if question in templates:
        return templates[question]["content"]

    return ''
    