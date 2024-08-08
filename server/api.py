
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
from uuid import uuid4


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

    @staticmethod
    def bad_final_response()->dict:
        return {
          "content": '哎呀，我思路有点乱，请重提问，多个点提示吧！',
          "mdData": '',
          "chartData": '',
          "sql": '',
        }

    @staticmethod
    def mk_chart_data(columns, rows, max_row=50)->dict:
        entity_name = dict()
        index_value = dict()
        chartData = dict()

        chartData['entity_name'] = entity_name
        chartData['index_value'] = index_value
        if len(columns) < 1:
            return chartData

        try:
            index = 0
            for row in rows:
                if index > max_row:
                    break

                items = [item for item in row]
                entity_name[index] = items[0]
                index_value[index] = float(items[-1])
                index+=1
        finally:
            return chartData, index



        

    


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
    rows, row_count = mysql.fetch(fmt_sql, conn)

    max_row_return = int(os.getenv("MAX_ROW_COUNT_RETURN", "50"))


    headers = bedrock_result['bedrockColumn']

    # 开始构建Markdown表格
    md_table = "| " + " | ".join(headers) + " |\n"

    # 添加分隔线
    md_table += "| " + " | ".join(["---" for _ in headers]) + " |\n"

    # 添加查询结果
    index = 0
    for row in rows:
        if index > max_row_return:
            break
        md_row = "| " + " | ".join([str(element) for element in row]) + " |"
        md_table += md_row + "\n"

        index +=1

    chart_data, chart_row_count = Helper.mk_chart_data(headers, rows, max_row_return)




    result = {
        "content":"\n",
        "mdData":md_table,
        "chartData":chart_data if chart_row_count > 1 else dict(),
        "sql":fmt_sql,
        "chartType":bedrock_result['chart_type'],
    }

    if row_count > max_row_return:
        bucket_name = os.getenv("BUCKET_NAME")
        load_url =  aws.upload_csv_to_s3(headers, rows, bucket_name, str(uuid4()))

        result['extra'] = f"由于数据量较大，当前只显示{max_row_return}行，全量数据请点击如下链接下载：\n{load_url}\n"

    print(result)

    return result






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
      "bedrockColumn": columns,
      "chart_type": parsed['chartType']
    }
    if is_hard_mode:
        result_j["reasoningFinal"] =parsed["reasoningFinal"]
        result_j["clarify"] =parsed["clarify"]
    return result_j


                                             

