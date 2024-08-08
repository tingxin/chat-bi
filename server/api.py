
import boto3


import os
import json

import re
from . import llm
from . import conf
from . import aws
from . import prompt_conf
from . import sql
from .db import mysql


class Helper:
    @staticmethod
    def format(raw:str):
        # 定义一个字典，将中文字符映射为英文字符
        char_mapping = {
            '“': ' ',  # 中文左双引号
            '”': ' ',   # 中文右双引号
            '‘': "'",  # 中文左单引号
            '’': "'",   # 中文右单引号
            '"': "'",  # 中文逗号
        }
        
        # 使用字典推导式和 join() 方法替换所有匹配的字符
        content = ''.join(char_mapping.get(char, char) for char in raw)
        
        return content

    @staticmethod
    def build_select_scenario_msg(question:str, promptConfig:dict)->str:

        question = Helper.format(question)
        if 'DefaultPrompt' in promptConfig and promptConfig['DefaultPrompt'] !="":
            content = f"{promptConfig['Overall']['ScenarioSelectionPrompt']} {promptConfig['Overall']['AllScenariosPrompt']} {promptConfig['DefaultPrompt']}。"
        else:
            content = f"{promptConfig['Overall']['ScenarioSelectionPrompt']} {promptConfig['Overall']['AllScenariosPrompt']}。"

        content += "你要回答的问题是:{" + question +"}。"
        return content

    @staticmethod
    def build_question_msg(question_str:str, scenario:str, prompt_conf:dict, is_hard_mode = False, rag_str=""):

        a = f"""{prompt_conf[scenario]['RolePrompt']} {prompt_conf[scenario]['TablePrompt']} {prompt_conf[scenario]['IndicatorsListPrompt']}
                {prompt_conf[scenario]['OtherPrompt']},示例输出结构  {prompt_conf['Examples']}。{rag_str}。
                {prompt_conf['ChartPrompt']}。
                """

        if is_hard_mode:
            a += prompt_conf['HardPrompt']

        a += f"。现在你要回答的问题是: {question_str}"
        return a


    @staticmethod
    def get_rag_str(question:str)->str:
        return ""

    @staticmethod
    def _bad_response()->dict:
        return {
            "bedrockSQL": None,
            "queryTableName":"",
            "bedrockColumn": '',
            "content": '哎呀，我思路有点乱，请重新问一次，多个点提示吧！'
        }

    def bad_final_response()->dict:
        return {
          "content": '哎呀，我思路有点乱，请重提问，多个点提示吧！',
          "mdData": '',
          "chartData": '',
          "sql": '',
        }
        

    


def get_result(msg:list,trace_id:str, mode_type: str ='normal'):
    prompt_content = prompt_conf.get("PROMPT_FILE_NAME")
    is_hard = mode_type == "bedrock-hard"
    bedrock_result =  answer(msg, prompt_content, trace_id, is_hard)

    if not bedrock_result['bedrockSQL'] or  bedrock_result['bedrockSQL'] == "ERROR: You can only read data.":
        return Helper.bad_final_response()

    fmt_sql = sql.format_md(bedrock_result['bedrockSQL'])
    print(f"{trace_id}========================>fmt sql is {fmt_sql}")

    # 默认查询澳洲站，后续要改
    db_info = conf.get_mysql_conf("au")
    conn = mysql.get_conn(db_info['host'], 3306, db_info['user'], db_info['pwd'], db_info['db'])
    rows = mysql.fetch(fmt_sql, conn)
    for item in rows:
        print(item)





def answer(
        msg:list, 
        promptConfig:dict,
        trace_id:str,
        is_hard_mode:bool):
    # 对问题进行提示词工程并查询bedrock
    bedrock = aws.get('bedrock-runtime')

    last_item = msg[-1]
    raw_content = last_item['content']
    scenario_str = Helper.build_select_scenario_msg(raw_content, promptConfig)
    print(f"formated msg=============>{msg}")

    rag_str = Helper.get_rag_str(last_item['content'])

    questions  = list()
    # questions.extend(msg)
    questions.append({
        "role":"user",
        "content": scenario_str
    })
    scenario = llm.query(questions,bedrock_client=bedrock)
    

    if scenario not in promptConfig:
        print(f"{trace_id}===============>failed to find scenario: {scenario}")
        return {
            "bedrockSQL": None,
            "queryTableName":scenario,
            "bedrockColumn": None,
            "content": "ERROR: No Table",
        }

    print(f"{trace_id}===============>{scenario} is selected")

    question_str = Helper.build_question_msg(raw_content,scenario,promptConfig,is_hard_mode, rag_str)
    questions  = list()
    # questions.extend(msg)
    questions.append({
        "role":"user",
        "content": question_str
    })

    result = llm.query(questions,bedrock_client=bedrock)
    result = llm.format_bedrock_result(result)

    
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        print(f"{trace_id}===================> 返回的结果不是json\n{result}")
        # 如果解析失败，返回False
        return Helper.bad_response()

    if  "finalSQL" not in parsed and  (parsed['finalSQL'] =="" or parsed['finalSQL'].find("ERROR: You can only read data.") >= 0):
        print(f"{trace_id}===================> 返回的结果没有生成SQL")
        return Helper.bad_response()

    if 'columnList' in parsed and isinstance(parsed["columnList"], list):
        columns = list()
        for item in parsed["columnList"]:
            parts = item.split(" AS ")
            if len(parts) > 1:
                columns.append(parts[1])
            else:
                columns.append(item)

        parsed["columnList"] = columns

    print(f"{trace_id}================> result is {result}")
    result_j = {
      "bedrockSQL": parsed['finalSQL'],
      "queryTableName": scenario,
      "bedrockColumn": columns
    }
    if is_hard_mode:
        result_j["reasoningFinal"] =parsed["reasoningFinal"]
        result_j["clarify"] =parsed["clarify"]
    return result_j


                                             

