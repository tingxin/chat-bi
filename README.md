
# 使用Bedrock 构建生成式BI
*代码原型使用aws rp团队*
![图示](assets/demo1.jpg)
## 快速体验
1. 配置环境变量
进入.env文件，根据注释提供aws ak, sk等信息

2. 启动docker
```
docker build -t text2sql_dev .

docker run --env-file=.env -p 5010:8900  --name textdemo1 text2sql
docker run --env-file=.env -p 5017:8900  --name textdemo2 text2sql_dev


docker build -f DockerfileServer -t text2sql_server .

docker run -p 5018:5018 -v ~/~work/chat-bi/logs:/app/logs  --name textdemoserver text2sql_server
```

使用浏览器打开
ip:5017



## 如何配置数据
1. 进入prompt文件夹
2. 参考README.md文件配置数据
3. 重新运行docker 


