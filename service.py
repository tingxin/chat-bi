from flask import Flask,request,jsonify
from flask_restful import Resource, Api
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


conf.load_env()
conf.load_sql_templates()


def load_prompt_conf():
    pass

# 创建一个资源
class HelloWorld(Resource):
    def get(self):
        # 返回一个简单的问候消息
        return {'message': 'Hello, World!'}


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
        data = service.get_result(json_data, trace_id,user_id, mtype)
        return data, 200

# 将资源添加到API端点
api.add_resource(QueryLLM, '/queryllm')

# 将资源添加到API端点
api.add_resource(HelloWorld, '/')


if __name__ == '__main__':
    server_host = os.getenv("SERVER_HOST","http://127.0.0.1:5020")
    index = server_host.find("://")
    server_host = server_host[index+3:]
    parts = server_host.split(":")
    host = parts[0]
    port = int(parts[1])
    app.run(debug=True, host=host, port=port)