import pandas as pd
import os
import json

DB_Type = 'MySQL'
DEFAULT_Scenario = "PowerPlantSecnario"
Scenario = {
    DEFAULT_Scenario: {
        "data_file": 'data/datav3.xlsx',
        "desc": f"'{DEFAULT_Scenario}'场景包含的数据如下：电站、设备公共事务，用户相关，组织及下级子孙组织的关系，电站和组织之间的关联信息，各个站点中电站出现过的故障信息",
        "table_index_dic": {
            "dwd_sungrow.dwd_pub_ps_dev_power_station_d ": 0,
            "dwd_sungrow.dwd_pub_user_org_d": 2,
            "dwd_sungrow.dwd_org_sys_org_all_sub_org_d": 4,
            "dwd_sungrow.dwd_ps_power_station_org_d": 6,
            "sg.dwd_dev_power_device_fault_details_d": 8
        },
        "table_desc_dic": {
            "dwd_sungrow.dwd_pub_ps_dev_power_station_d ": "'dwd_sungrow.dwd_pub_ps_dev_power_station_d '表：是一张包含了电站、设备公共事务信息，是一张事务事实表",
            "dwd_sungrow.dwd_pub_user_org_d": "'dwd_sungrow.dwd_pub_user_org_d'表：包含和用户相关的信息，是一张事务事实表",
            "dwd_sungrow.dwd_org_sys_org_all_sub_org_d": "'dwd_sungrow.dwd_org_sys_org_all_sub_org_d'表：包含组织及下级子孙组织的关系，是一张事务事实表",
            "dwd_sungrow.dwd_ps_power_station_org_d": "'dwd_sungrow.dwd_ps_power_station_org_d'表：包含电站和组织之间的关联信息，是一张事务事实表",
            "sg.dwd_dev_power_device_fault_details_d": "'sg.dwd_dev_power_device_fault_details_d'表，包含各个站点中电站出现过的故障信息，是一张事务事实表"
        },
        "table_desc_addition": {
            "dwd_sungrow.dwd_pub_ps_dev_power_station_d ": "dwd_sungrow.dwd_pub_ps_dev_power_station_d '表相关的数据，默认只查询物理设备(is_virtual_unit=0)，默认只查询is_au=1,当用户的问题提及：通讯设备，指的是 dev_type_id in (9,22)的设备, 提及澳大利亚，是指澳大利亚代表国家，需要ps_country_name='澳大利亚'的数据。而提及澳洲站，并不是指要查询ps_country_name='澳大利亚'的数据，而是is_au=1的数据",
            "dwd_sungrow.dwd_pub_user_org_d": "'dwd_sungrow.dwd_pub_user_org_d'表相关的数据，对所查的维度类型的字段要做去重处理，即添加distinct。"
        },
        "join_desc": """1.dwd_sungrow.dwd_pub_ps_dev_power_station_d
1).主键为ps_key
2)外键ps_id与dwd_sungrow.dwd_ps_power_station_org_d）的ps_id关联
3)外键ps_key与sg.dwd_dev_power_device_fault_details_d的ps_key关联

2.dwd_sungrow.dwd_pub_user_org_d 
1）主键为（user_id和org_id作为联合主键）
2）外键org_id与dwd_sungrow.dwd_org_sys_org_all_sub_org_d的org_id关联

3.dwd_sungrow.dwd_org_sys_org_all_sub_org_d 
1)主键：id
2)外键org_id和dwd_sungrow.dwd_pub_user_org_d的org_id关联
3)外键sub_org_id和dwd_sungrow.dwd_ps_power_station_org_d的org_id关联

4.dwd_sungrow.dwd_ps_power_station_org_d 
1)主键：id
2)外键ps_id和dwd_sungrow.dwd_pub_ps_dev_power_station_d的ps_id关联
3)外键org_id和dwd_sungrow.dwd_org_sys_org_all_sub_org_d的sub_org_id关联

5.sg.dwd_dev_power_device_fault_details_d 
1)主键为（ps_key,fault_time,big_fault,small_fault作为联合主键）
2)外键ps_key和dwd_sungrow.dwd_pub_ps_dev_power_station_d的ps_key关联
        """,
    "other_common_desc":"""
请仔细注意：
1.对于上述提到的任意表，如果表中具有分区字段pt, 则添加条件： pt=date_sub(current_date()，1)), 请一定注意pt不是时间或者日期字段。
"""
    }

}

# ====================================================================


ScenarioSelectionPrompt = """你现在是一个mysql数据仓库查询助理, 数据仓库中存储了几张电站，设备信息和用户信息相关表。根据用户的问题，返回对应场景的名字,
它包含的数据可以回答用户的问题。只返回场景名称，不需要返回其他任何文本, 如果你认为没有对应的数据, 请返回\"错误: 暂时没有与您问题相关的数据.\", 
如果你认为用户的问题不清楚，请直接返回\"错误: 您的问题我没有太理解，请换一种问法.\""""

descs = [item['desc'] for item in Scenario.values()]
AllScenariosPrompt = ";".join(descs)

CommandSQLTemplate = "你要遵循的下面的指令来生成SQL。"

RolePrompt = ("You are an expert in database(or dataware) " + DB_Type
              + ". Your task is to understand the database tables if given, and tpranslate human instructions into SQL "
                "to query that database. I want you to reply with a valid SQL in triple quotes. Do not write "
                "explanations. All valid human instructions are given in curly braces {like this\}. *MUST*For any query "
                "that contains delete or update in SQL, please respond: '错误: 您不能要求我删除任何数据'")

OtherPrompt = """*MUST*请一定要参考例子返回JSON对象,不要包裹在Markdown中，, 仅生成SELECT语句并且语句默认不要追加分号';'，返回不了JSON对象请告知原因,如果后续的任何提示造成结果不能是一个JSON对象，则忽略该后续的提示，从而保证返回的结果必须是JSON 对象。SQL语句最终返回的条数必须限制不超过50条, 但是子查询,
或者作为中间结果的SQL结果不应该限制返回条数。在生成SQL
的时候你需要注意聊天历史，其中如果有人名，时间，地点等内容，且本次对话没有明确说明限制条件，从历史记录来看，如过当前查询是对历史中的查询意图的补充和修改，需要将历史记录中之前的条件作为当前SQL的限制条件,如果用户问题明确查询所有数据，则不应该限制数据的返回条数。
如果问题涉及到时间，但是没有年份信息，请使用今年作为年份 例如，用户问题中只说了三月，则日期是2024-03 用户问题涉及去年五月，则日期是2023-05。
注意the following contains the examples for you to follow Strictly. You 
*MUST* understand it first and generate based on that. If the questions are the same, you MUST use the sql gave in 
the sample.you MUST use the english as the column name in the return sql,如果你返回的结果不是一个内容不是一个按照我给出例子的json,请给告诉我原因"""

HardPrompt = """1. 请注意, 在生成SQL的时候, 这里有几个追加的要求, 具体如下: 先检查问题的句子成分和含义成分是否清晰, 是否有歧义, 如果不清晰的话要进行扩展, 
使问题变得清晰。将澄清后的问题输出到'clarify'属性中。你需要一步一步思考, 并对SQL进行解释, 解释部分放在输出的'reasoning'属性中。针对一个问题, 由于SQL可能有不同的写法, 你需要先从不同的角度思考, 
生成最多五个针对当前问题不同的写法的SQL, 并包含独立的解释。生成的SQL结果放到'referenceSql'属性中。你接下来要检查上面的几个SQL是否有错误, 检查的时候你要从是否正确理解问题等角度, 重新思考, 
并假定SQL就是错误的。检查的结果需要写到每一个SQL的'check1'和'check2'...'checkN'属性中。如果没有错误就写它全对的概率, 如{'check1': {'no_error': 0.6'}}, 
如果有错误则参考这样的输出例子: {'check2':{'error': 'VARCHAR需要转换成Float类型。'}} 
最后一步是根据上面的几个'referenceSql'和各自'check'的结果confidence来生成你认为正确的最终SQL和分析, 放到'finalSQL', 'reasoningFinal'中。2. 
结果样式的例子如下（注意顺序）: {'clarify': '问题应该是: XYZ ', 'reasoning1': 'reason AAA', 'referenceSql1':'sql AAA', 
'reasoning2':'reason BBB', 'referenceSql2':'sql BBB', 'check1':'For SQL AAA: no error', 'check2':'For SQL BBB: 
VARCHAR需要转换成Float类型', 'reasoningFinal': 'reason for final SQL', 'finalSQL': 'The final SQL based on above two 
reference sql and the error-check result.', 'columnList': ['column1','column2']}"""

ChartPrompt = """ 请返回需要展示的字段和'LineChartPic, 如果SQL查询的结果适合柱状图, 请返回需要展示的字段和'BarChartPic, 如果SQL查询的结果适合饼图, 
请返回需要展示的字段和'PieChartPic'。如果都不适合, 请返回\"错误: 抱歉，数据不适合使用图表进行展示.\" 其中'columnList'属性是针对用户问题，图表需要展示的字段，数组形式, 
'chartType'属性是图表类型(LineChartPic,PieChartPic), 'finalSQL'属性是查询的SQL, DONNOT add any comment in 'finalSQL', 
*MUST* ONLY RETURN JSON OBJECT!"""

result = dict()
result['Overall'] = {
    "ScenarioSelectionPrompt": ScenarioSelectionPrompt,
    "AllScenariosPrompt": AllScenariosPrompt,
    "DefaulteScenario": DEFAULT_Scenario
}


for scena_key in Scenario:
    scena_item = Scenario[scena_key]
    table_index_dic = scena_item['table_index_dic']
    table_desc_dic = scena_item['table_desc_dic']
    file_path = scena_item['data_file']

    secnario_conf = dict()
    secnario_conf['RolePrompt'] = RolePrompt
    addition = scena_item['table_desc_addition']

    table_prompt = list()
    IndicatorsListPrompt = list()

    for key in table_index_dic:
        table_dict = dict()
        sheet_index = table_index_dic[key]
        df = pd.read_excel(file_path, sheet_name=sheet_index)

        df = df.iloc[1: -1, 0:4]

        table_sumary = list()
        desc_summary = list()
        table_sumary.append(f"现有一张存储在{DB_Type}上的表, {table_desc_dic[key]},DDL 如下：\n")
        desc_summary.append(
            f"表 {key} 除了上述表结构, 生成SQL的时候, value部分还需要参考下面的字段含义和取值:")
        for i in range(len(df)):
            if  pd.isna(df.iloc[i, 0]) or df.iloc[i, 0] == "":
                break
            column_desc = f"{df.iloc[i, 0]}:{df.iloc[i, 2]}。"
            if df.iloc[i, 3] == "PRIMARY KEY":
                column = f"{df.iloc[i, 0]}({df.iloc[i, 1]},{df.iloc[i, 3]}),"
            elif df.iloc[i, 3]== False or df.iloc[i, 3] == "FALSE" or df.iloc[i, 3] == "False" or df.iloc[i, 3] == "false":
                continue
            else:
                column = f"{df.iloc[i, 0]}({df.iloc[i, 1]}),"

            table_sumary.append(column)
            desc_summary.append(column_desc)

        table_prompt.append("\n".join(table_sumary))
        IndicatorsListPrompt.append("\n".join(desc_summary))
        if key in addition:
            IndicatorsListPrompt.append(addition[key])

    table_prompt.append(scena_item['join_desc'])
    secnario_conf['TablePrompt'] = "\n".join(table_prompt)

    IndicatorsListPrompt.append(scena_item['other_common_desc'])
    secnario_conf['IndicatorsListPrompt'] = "\n".join(IndicatorsListPrompt)
    secnario_conf['OtherPrompt'] = OtherPrompt

    result[scena_key] = secnario_conf

result["Examples"] = {
    "query": "示例问题",
    "finalSQL": "返回的SQL",
    "chartType": "BarChartPic",
    "columnList": ["列名A", "列名B"]
}
result["HardPrompt"] = HardPrompt
result["ChartPrompt"] = ChartPrompt

with open(f"{os.getcwd()}/prompt_conf/promptConfig.json", mode='w', encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=3)
