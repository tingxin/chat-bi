from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # 解析请求的URL
        parsed_path = urllib.parse.urlparse(self.path)
        # 检查请求的URL是否是允许访问的文件
        if parsed_path.path.endswith(".csv"):
            # 调用父类的do_GET方法来处理请求
            super().do_GET()
        else:
            # 如果请求的不是允许的文件，则返回403禁止访问
            self.send_error(403, "Forbidden: Access is denied.")

    def list_directory(self):
        # 重写list_directory方法，禁止列出目录
        self.send_error(403, "Forbidden: Access is denied.")

# 设置服务器的端口和处理程序
server_address = ('', 5011)
httpd = HTTPServer(server_address, CustomHTTPRequestHandler)

# 启动服务器
print("Serving HTTP on port 5011...")
httpd.serve_forever()