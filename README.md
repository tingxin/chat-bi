
# 使用Bedrock 构建生成式BI
*代码原型使用aws rp团队*
![图示](assets/demo1.jpg)
## 快速体验
1. 配置环境变量
进入.env文件，根据注释提供aws ak, sk等信息

2. 启动docker
```
docker build -t text2sql_dev .

docker run --env-file=.env -p 5017:8900  --name textdemo2 text2sql_dev


docker build -f DockerfileServer -t text2sql_server .

docker run -p 5018:80 -v ~/work/chat-bi/logs:/app/logs  --name textdemoserver text2sql_server

```

使用浏览器打开
ip:5017



## 如何配置数据
1. 进入prompt文件夹
2. 参考README.md文件配置数据
3. 重新运行docker 


## 自动生成提示词
python3 prompt_gen.py template --scenario nitto --tables nitto_order nitto_fiscal_year be_busi_fee_result

python3 prompt_gen.py prompt


## 其他
mysql -h tx-db.cbore8wpy3mc.us-east-2.rds.amazonaws.com -P 3306 -u reader -p 

CREATE USER 'reader'@'%' IDENTIFIED BY 'reader#1234';
ALTER USER 'reader'@'%' IDENTIFIED BY 'Reader2025';

GRANT SELECT ON *.* TO 'reader'@'%';




