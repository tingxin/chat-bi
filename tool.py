from prompt import loader
from server import conf
import os
from server.db import mysql


conf.load_env()

bucket_name = os.getenv("BUCKET_NAME")
example_file = os.getenv("EXAMPLE_FILE_NAME")
prompt_file = os.getenv("PROMPT_FILE_NAME")
rag_file = os.getenv("RAG_FILE_NAME")


data_files = f"{os.getcwd()}/prompt/data/rawdata/nitto_v3.xlsx"
save_to_path = f"{os.getcwd()}/prompt/prompt_conf"


db_infos = conf.get_mysql_conf_by_question('nitto')
db_info = db_infos[0]
conn = mysql.get_conn(
        db_info['host'], db_info['port'], db_info['user'], db_info['pwd'], db_info['db'])

loader.load_from_excel(data_files, "be_busi_fee_result", conn, 1)