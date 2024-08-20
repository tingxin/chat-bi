
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
import pandas as pd


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
            content = f"{promptConfig['Overall']['AllScenariosPrompt']} {promptConfig['Overall']['ScenarioSelectionPrompt']} {promptConfig['DefaultPrompt']}。"
        else:
            content = f"{promptConfig['Overall']['AllScenariosPrompt']} {promptConfig['Overall']['ScenarioSelectionPrompt']}。"

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
    def bad_response(error:str="")->dict:
        r  = {
            "content": '哎呀，我思路有点乱，请重新问一次，多个点提示吧！'
        }
        if error !="":
            r["error"] = error

        return r


    @staticmethod
    def mk_chart_data(columns, columns_type, db_results, max_row=50)->dict:
        entity_name = dict()
        index_value = dict()
        chartData = dict()

        chartData['entity_name'] = entity_name
        chartData['index_value'] = index_value
        # 前端UI 暂时只支持一个度量，一个维度
        if len(columns) != 2 or "rows" not in db_results:
            return chartData

        # 前端目前只支持一个维度，一个度量
        if columns_type[0] == columns_type[1]:
            return chartData
       
        rows = db_results["rows"]
        try:
            index = 0
            for row in rows:
                if index > max_row:
                    break
                
                items = [item for item in row]
                for i in range(0, len(columns)):
                    if columns_type[i] == "度量":
                        index_value[index] = float(items[i])
                    else:
                        entity_name[index] = str(items[i])
                index+=1
        finally:
            return chartData

        
        
        
    
    @staticmethod
    def query_db(db_info:dict, fmt_sql:str):
        print(f"=======================>正在查询{db_info['desc']}的数据")
        conn = None
        try:
            conn = mysql.get_conn(db_info['host'], db_info['port'], db_info['user'], db_info['pwd'], db_info['db'])
            rows, row_count = mysql.fetch(fmt_sql, conn)
            return {
                "rows":rows,
                "row_count":row_count,
                "desc":db_info["desc"]
            }
        except Exception as ex:
            print(f"=====================>查询数据出现异常{fmt_sql}：\n{ex}")
            return {
                "row_count":0
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def query_db_async(db_info:dict, fmt_sql:str, result_queue:Queue):
        print(f"=======================>正在查询{db_info['desc']}的数据")
        conn = None
        try:
            conn = mysql.get_conn(db_info['host'], db_info['port'], db_info['user'], db_info['pwd'], db_info['db'])
            df = pd.read_sql(fmt_sql, conn) 
            r = {
                "rows":df,
                "row_count":len(df)
            }
            result_queue.put(r)
        except Exception as ex:
            print(f"=====================>查询数据出现异常{fmt_sql}：\n{ex}")
            r = {
                "row_count":0
            }
        finally:
            if conn:
                conn.close()
        

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
            if "rows" in db_result:
                db_results.append(db_result)
        
        return db_results

    @staticmethod
    def merge_data(db_results:list, columns:list, columns_type:list):
        if len(db_results) == 0:
            return {
            "rows":[],
            "row_count":0
        }

        dfs = [item["rows"] for item in db_results]

        merged_df = pd.concat(dfs, ignore_index=True)

        # 假设dimension1和dimension2是维度，measure1和measure2是度量  
        dimensions = list() 
        measures = list() 

        for index in range(0, len(columns)):
            if columns_type[index] =="度量":
                measures.append(columns[index])
            else:
                dimensions.append(columns[index])

        # 按照维度分组，并对度量求和  
        aggregated_df = merged_df.groupby(dimensions)[measures].sum().reset_index()
        # 查看聚合后的数据  
        records = aggregated_df.to_records(index=False).tolist()

        return {
            "rows":records,
            "row_count":len(records)
        }





    @staticmethod
    def mk_md_table(headers:list, db_result:list, max_row_return:int):

        # 开始构建Markdown表格
        md_table = "| " + " | ".join(headers) + " |\n"

        # 添加分隔线
        md_table += "| " + " | ".join(["---" for _ in headers]) + " |\n"

        index = 0

        if "rows" in db_result:
            rows = db_result["rows"]
            for row in rows:
                if index >= max_row_return:
                    break
                md_row = "| " + " | ".join([str(element) for element in row]) + " |"
                md_table += md_row + "\n"

                index +=1

        return md_table


def get_result(msg:list,trace_id:str, mode_type: str ='normal'):
    bedrock = aws.get('bedrock-runtime')
    bedrock_result = answer_template_sql(bedrock, msg, trace_id)
    if "error" in bedrock_result:

        prompt_content = prompt.get("PROMPT_FILE_NAME")
        # is_hard = mode_type == "bedrock-hard"
        is_hard = True
        bedrock_result =  answer(bedrock, msg, prompt_content, trace_id, is_hard)

    if "error" in bedrock_result:
        return  {
            "content":bedrock_result["error"],
            "mdData":"",
            "chartData":dict(),
            "sql":"",
            "chartType":""
        }

    fmt_sql = sql.format_md(bedrock_result['bedrockSQL'])
    print(f"{trace_id}========================>fmt sql is {fmt_sql}")

    last_item = msg[-1]
    raw_content = last_item['content']

    max_row_return = int(os.getenv("MAX_ROW_COUNT_RETURN", "50"))

    db_infos = conf.get_mysql_conf_by_question(raw_content)
    

    columns = bedrock_result['bedrockColumn']
    column_types = bedrock_result['column_type']
    if len(db_infos) == 1:
        db_info = db_infos[0]
        db_results =Helper.query_db(db_info, fmt_sql)
    else:
        db_results= Helper.query_many_db(db_infos, fmt_sql)
        db_results = Helper.merge_data(db_results, columns, column_types)

    cn_columns = bedrock_result['cn_column']
    md_table = Helper.mk_md_table(cn_columns, db_results, max_row_return)

    print(column_types)
    chart_data = Helper.mk_chart_data(cn_columns,column_types, db_results, max_row_return)

    chartType ="BarChartPic" if bedrock_result['chart_type'].find("错误") >=0 else bedrock_result['chart_type']

    result = {
        "mdData":md_table,
        "chartData":chart_data,
        "sql":fmt_sql,
        "chartType":chartType,
    }

    if "clarify" in bedrock_result:
        result['content'] = bedrock_result['clarify']
        

    total_row_count = db_results["row_count"]
    if total_row_count >= max_row_return:
        # 数据量太大，则保存到s3，生成下载链接让客户后台下载
        bucket_name = os.getenv("BUCKET_NAME")
        load_url =  aws.upload_csv_to_s3(cn_columns, db_results, bucket_name, str(uuid4()))

        result['extra'] = load_url
        result['content'] =result['content'] +f"\n数据量较大，默认只显示了 {max_row_return}, 请点击下载查看全部数据。建议使用汇总数据而非明细数据分析"
    else:
        result['extra'] = ""

    return result



def answer(
        bedrock,
        msg:list, 
        promptConfig:dict,
        trace_id:str,
        is_hard_mode:bool):
    # 对问题进行提示词工程并查询bedrock
    print([item['role'] for item in msg])
    last_item = msg[-1]
    raw_content = last_item['content']
    scenario_str = Helper.build_select_scenario_msg(raw_content, promptConfig)

    rag_str = Helper.get_rag_str(last_item['content'])

    questions  = list()
    # questions.extend(msg)
    questions.append({
        "role":"user",
        "content": scenario_str
    })
    print("begin select scenario")
    scenario = llm.query(questions,bedrock_client=bedrock)
    

    if scenario not in promptConfig:
        # 如果有默认场景就尝试使用默认场景
        if 'DefaulteScenario' in promptConfig:
            error = f"{trace_id}===============>没有找到合适的场景: {scenario}，尝试使用默认场景查询{promptConfig['DefaulteScenario']}"
            print(error)
            scenario = promptConfig['DefaulteScenario']
        else:
            error = f"{trace_id}===============>failed to find scenario in prompt config file: {scenario}"
            print(error)
            return Helper.bad_response(error=error)
        

    print(f"{trace_id}===============>{scenario} is selected")
               

    question_str = Helper.build_question_msg(raw_content,scenario,promptConfig,is_hard_mode, rag_str)
    questions  = list()
    # questions.extend(msg)
    history_count = int(os.getenv("HISTORY_COUNT", 5))

    
    if len(msg) - history_count>=0:
        begin_index = len(msg) - history_count
        bound = history_count
    else:
        begin_index = 0
        bound = len(msg)

    # 第一和最后一个都必须是user 发起的提问
    msg_first = msg[begin_index]
    if msg_first['role'] !="user":
        begin_index = begin_index -1
        bound = bound + 1
    

    for i in range(0, bound -1):
        msg_item = msg[begin_index + i]
        
        if msg_item["role"] == "assistant":
            if "clarify" in msg_item:
                q = msg_item['clarify']
            else:
                q = "查询完毕"
        else:
            q = msg_item["content"]

        questions.append({
            "role":msg_item["role"],
            "content": q
        })

    questions.append({
        "role":"user",
        "content": question_str
    })

    result = llm.query(questions,bedrock_client=bedrock)
    result = llm.format_bedrock_result(result)

    
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        error = f"{trace_id}===================> 返回的结果不是json\n{result}"
        print(error)
        return Helper.bad_response(error=error)

    if  "finalSQL" not in parsed and  (parsed['finalSQL'] =="" or parsed['finalSQL'].find("ERROR: You can only read data.") >= 0):

        error = f"{trace_id}===================> 返回的结果没有生成SQL"
        print(error)
        return Helper.bad_response(error=error)

    if 'columnList' in parsed and isinstance(parsed["columnList"], list):
        columns = list()
        for item in parsed["columnList"]:
            parts = item.split(" AS ")
            if len(parts) > 1:
                columns.append(parts[1])
            else:
                columns.append(item)

        parsed["columnList"] = columns
    print(parsed)

    result_j = {
      "bedrockSQL": parsed['finalSQL'],
      "queryTableName": scenario,
      "bedrockColumn": columns,
      "cn_column":parsed['columnCNList'],
      "column_type": parsed['columnType'],
      "chart_type": parsed['chartType']
    }
    if is_hard_mode:
        result_j["clarify"] =parsed["clarify"]
    return result_j


def answer_template_sql(
        bedrock,
        msg:list, 
        trace_id:str):

    # 对问题进行提示词工程并查询bedrock
    last_item = msg[-1]
    raw_content = last_item['content']


    # 开始查询问题对应的模板问题
    question_prompt = prompt.template_question(raw_content)

    questions  = list()
    # questions.extend(msg)
    questions.append({
        "role":"user",
        "content": question_prompt
    })


    result = llm.query(questions,bedrock_client=bedrock)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        error  = f"{trace_id}===================> 没有找到模板问题\n{result}"
        print(error)
        # 如果解析失败，返回False
        return Helper.bad_response(error)
    

    if "error" in parsed or not bool(parsed["result"]):
        error  = f"{trace_id}===================> 没有找到模板问题\n{parsed['reason']}"
        print(error)
        # 如果解析失败，返回False
        return Helper.bad_response(error)


    template_question = parsed["question"]
    params = parsed["params"]

    # 获取模板问题对应的模板SQL
    template_sql = prompt.template_sql(template_question)
    if template_sql == "":
        error  = f"{trace_id}===================> 模板SQL为空\n{template_question}"
        print(error)
        # 如果解析失败，返回False
        return Helper.bad_response(error)
    
    fmt_sql = template_sql.format(*params)

    sql_column_prompt = prompt.template_sql_columns(fmt_sql, raw_content)

    questions  = list()
    # questions.extend(msg)
    questions.append({
        "role":"user",
        "content": sql_column_prompt
    })
    result = llm.query(questions,bedrock_client=bedrock)
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        error  = f"{trace_id}===================> 没有找到模板sql列信息\n{result}"
        print(error)
        return Helper.bad_response(error)

    columns = parsed["columns"]
    columns_ype = parsed["columns_type"]
    
    result_j = {
      "bedrockSQL": fmt_sql,
      "queryTableName": "template",
      "bedrockColumn": columns,
      "column_type": columns_ype,
      "chart_type": "BarChart"
    }
    return result_j


    

    

                                             
