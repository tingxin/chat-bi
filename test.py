from server import prompt
from server.conf import load_env, load_sql_templates
from server import aws, llm
import json

load_env()
load_sql_templates()

def chat():
    raw_content = "用户账号为88888下机型是p123和sg456的组织id、组织名称、电站id"
        # 对问题进行提示词工程并查询bedrock
    bedrock = aws.get('bedrock-runtime')

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
        print(f"===================> 没有找到模板问题\n{result}")
        # 如果解析失败，返回False
        return ""
    
    # template_question = parsed["question"]
    # columns = parsed["params"]

    # template_sql = prompt.template_sql(template_question)
    # if template_sql == "":
    #     return ""
    
    # fmt_sql = template_sql.format(*columns)

    # sql_column_prompt = prompt.template_sql_columns(fmt_sql, raw_content)

    # questions  = list()
    # # questions.extend(msg)
    # questions.append({
    #     "role":"user",
    #     "content": sql_column_prompt
    # })
    # result = llm.query(questions,bedrock_client=bedrock)
    # try:
    #     parsed = json.loads(result)
    # except json.JSONDecodeError:
    #     print(f"===================> 没有找到模板sql列信息\n{result}")
    #     # 如果解析失败，返回False
    #     return ""

    print(parsed)
    

   

chat()


