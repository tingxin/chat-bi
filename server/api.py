
import boto3


import os
import json

import re
from . import llm
from . import conf
from . import aws
from . import prompt
from . import sql
from .db import mysql
from uuid import uuid4
import threading
from queue import Queue
from pandas import DataFrame



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

        
        
        
    
    @staticmethod
    def query_db(db_info:dict, fmt_sql:str):
        print(f"=======================>正在查询{db_info['desc']}的数据")
        conn = mysql.get_conn(db_info['host'], 3306, db_info['user'], db_info['pwd'], db_info['db'])
        rows, row_count = mysql.fetch(fmt_sql, conn)
        return {
            "rows":rows,
            "row_count":row_count,
            "desc":db_info["desc"]
        }

    @staticmethod
    def query_db_async(db_info:dict, fmt_sql:str, result_queue:Queue):
        print(f"=======================>正在查询{db_info['desc']}的数据")
        conn = mysql.get_conn(db_info['host'], 3306, db_info['user'], db_info['pwd'], db_info['db'])
        rows, row_count = mysql.fetch(fmt_sql, conn)
        r = {
            "rows":rows,
            "row_count":row_count,
            "desc":db_info["desc"]
        }
        result_queue.put(r)

    @staticmethod
    def query_many_db(db_infos:list, fmt_sql:str)->list:
        threads = []
        result_queue = Queue()
        for db_info in db_infos:
            # 从连接池获取连接
            thread = threading.Thread(target=Helper.query_db_async, args=(db_info, fmt_sql, result_queue))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        db_results = list()
        while not result_queue.empty():
            db_result = result_queue.get()
            db_results.append(db_result)
        
        return db_results

    @staticmethod
    def mk_md_table(headers:list, db_results:list, max_row_return:int):

        if len(db_results) > 1:
            headers.insert(0, "站点")

        # 开始构建Markdown表格
        md_table = "| " + " | ".join(headers) + " |\n"

        # 添加分隔线
        md_table += "| " + " | ".join(["---" for _ in headers]) + " |\n"

        index = 0
        if len(db_results) > 1:
            # 如果是多个数据源返回的数据，则添加站点信息
            
            for db_result in db_results:
                if index > max_row_return:
                    break
                
                rows, row_count,desc = db_result["rows"], db_result["row_count"],db_result["desc"]
                for row in rows:
                    if index > max_row_return:
                        break

                    md_row = f"| {desc} | " + " | ".join([str(element) for element in row]) + " |"
                    md_table += md_row + "\n"

                    index +=1
        else:
            db_result = db_results[0]
            rows, row_count,desc = db_result["rows"], db_result["row_count"],db_result["desc"]
            for row in rows:
                if index > max_row_return:
                    break
                md_row = "| " + " | ".join([str(element) for element in row]) + " |"
                md_table += md_row + "\n"

                index +=1

        return md_table


def get_result(msg:list,trace_id:str, mode_type: str ='normal'):
    prompt_content = prompt.get("PROMPT_FILE_NAME")
    is_hard = mode_type == "bedrock-hard"
    bedrock_result =  answer(msg, prompt_content, trace_id, is_hard)

    if not bedrock_result['bedrockSQL'] or  bedrock_result['bedrockSQL'] == "ERROR: You can only read data.":
        return Helper.bad_final_response()

    fmt_sql = sql.format_md(bedrock_result['bedrockSQL'])
    print(f"{trace_id}========================>fmt sql is {fmt_sql}")

    last_item = msg[-1]
    raw_content = last_item['content']

    max_row_return = int(os.getenv("MAX_ROW_COUNT_RETURN", "50"))

    db_infos = conf.get_mysql_conf_by_question(raw_content)
    

    if len(db_infos) == 1:
        db_info = db_infos[0]
        db_result =Helper.query_db(db_info, fmt_sql)
        db_results=[db_result]
    else:
        db_results= Helper.query_many_db(db_infos, fmt_sql)


    headers = bedrock_result['bedrockColumn']
    md_table = Helper.mk_md_table(headers, db_results, max_row_return)

    if len(db_results) ==1:
        rows = db_results[0]["rows"]
        chart_data, chart_row_count = Helper.mk_chart_data(headers, rows, max_row_return)
    else:
        chart_data, chart_row_count = dict(),0


    result = {
        "content":"\n",
        "mdData":md_table,
        "chartData":chart_data if chart_row_count > 1 else dict(),
        "sql":fmt_sql,
        "chartType":bedrock_result['chart_type'],
    }

    total_row_count = sum([item["row_count"] for item in db_results])
    if total_row_count > max_row_return:
        # 数据量太大，则保存到s3，生成下载链接让客户后台下载
        bucket_name = os.getenv("BUCKET_NAME")
        load_url =  aws.upload_csv_to_s3(headers, db_results, bucket_name, str(uuid4()))

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


                                             

