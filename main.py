from flask import Flask,request,jsonify
from flask_restful import Resource, Api
from urllib.parse import unquote
import boto3
from server import conf, prompt
import os
import requests
from server import api as service
import json

# 创建Flask应用
app = Flask(__name__)
# 创建API对象
api = Api(app)


conf.load_env(f"{os.getcwd()}/.env")
conf.load_sql_templates()
service.init()

class QueryLLM(Resource):
    def get(self):
        # 从请求参数中获取查询字符串
        query = request.args.get('query', '')
        # 执行查询
        result = {
            "data":query
        }
        # 返回查询结果
        return jsonify(result)


    def post(self):
        # 接收 JSON 数据
        json_data = request.get_json()
        mtype = request.args.get('mtype', '')
        trace_id = request.headers.get('X-Trace-Id')
        user_id = request.headers.get('X-User-Id')
        user_id = unquote(user_id)

        # 阳光电源特有场景，要下载大量数据
        attachments = service.get_attachment(user_id)
        if attachments:
            check_ids = attachments.split("\n")
            check_ids = [item.strip() for item in check_ids if item!='']
            if check_ids:
                data = service.get_result(json_data, trace_id,user_id, mtype, check_ids)
                return data, 200
            
        data = service.get_result(json_data, trace_id,user_id, mtype)
        return data, 200


class UploadFile(Resource):
    def post(self):
        raw_data = request.get_data()
        post_data_str = raw_data.decode('utf-8')
        user_id = request.headers.get('X-User-Id')
        user_id = unquote(user_id)
        if user_id:
            service.set_cache(user_id, post_data_str)
        return {}, 200

            
# 将资源添加到API端点
api.add_resource(QueryLLM, '/queryllm')
api.add_resource(UploadFile, '/upload')



if __name__ == '__main__':
    server_host = os.getenv("SERVER_HOST","http://127.0.0.1:5020")
    index = server_host.find("://")
    server_host = server_host[index+3:]
    parts = server_host.split(":")
    host = parts[0]
    port = int(parts[1])
    app.run(host="0.0.0.0", port=port)
