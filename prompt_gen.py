from prompt import tool
from server import conf, aws
import os
import json


conf.load_env()



bucket_name = os.getenv("BUCKET_NAME")

# EXAMPLE_FILE_NAME=demo/defaultDragonPrompt.json
# PROMPT_FILE_NAME=demo/promptConfig.json
# RAG_FILE_NAME=demo/ragSampleList.json

example_file=os.getenv("EXAMPLE_FILE_NAME")
prompt_file=os.getenv("PROMPT_FILE_NAME")
rag_file=os.getenv("RAG_FILE_NAME")


data_files = f"{os.getcwd()}/prompt/data"
save_to_path = f"{os.getcwd()}/prompt/prompt_conf"


prompt_file_name=prompt_file.split("/")[1]
example_file_name=example_file.split("/")[1]
rag_file_name=rag_file.split("/")[1]

prompt_path = save_to_path +"/" + prompt_file_name
example_path = save_to_path +"/" + example_file_name
rag_path = save_to_path +"/" + rag_file_name

tool.run(data_files, prompt_path)

aws.upload_file_to_s3(prompt_path,bucket_name, prompt_file)
aws.upload_file_to_s3(example_path,bucket_name, example_file)
aws.upload_file_to_s3(rag_path,bucket_name, rag_file)





