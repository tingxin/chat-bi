
# 使用Bedrock 构建生成式BI
*代码原型使用aws rp团队*
![图示](assets/demo1.jpg)
## 快速体验
1. 配置环境变量
进入.env文件，根据注释提供aws ak, sk等信息

2. 启动docker
```
# build 前端
docker build -t text2sql_dev .

# 启动前端
docker run --env-file=.env -p 5017:8900  --name textdemo2 text2sql_dev

# build后端
docker build -f DockerfileServer -t text2sql_server .

# 启动后端
docker run -p 5018:80 -v ~/work/chat-bi/logs:/app/logs  --name textdemoserver text2sql_server

```

使用浏览器打开
ip:5017

## 自动化测试
1. 编写测试脚本，脚本内容为
你的用户问题，和你期望生成的sql.脚本以excel文件保存在
```
/server/testcases/
```
参考
```
/server/testcases/sql_testcase1.xlsx
```

2. 执行
```
python3 test.py
```
3. 请在生成的日志log/chatbi_test.log中查看和分析结果

## 自动生成提示词
prompt_gen.py文件为生成提示词的入口文件

### 第一步，生成提示词模板文件
命令
```
python3 prompt_gen.py -h

提示词生成辅助工具

positional arguments:
  {template,prompt}  可用命令
    template         生成提示词模板，供人工review
    prompt           生成提示词文件，并上传到S3中，执行前请确保已经生成了提示词模板，并人工进行reivw

options:
  -h, --help         show this help message and exit

```
生成提示词模板
```
python3 prompt_gen.py template -h
usage: prompt_gen.py template [-h] [--scenario SCENARIO]
                              [--tables TABLES [TABLES ...]]

options:
  -h, --help            show this help message and exit
  --scenario SCENARIO   场景名称
  --tables TABLES [TABLES ...]
                        数据表列表，表名称之间用空格隔开
```
例如：
```
python3 prompt_gen.py template --scenario demo --tables order_detail user goods
```

生成的提示词模板文件是一个excel文件位于
```
prompt/data/promptdata
```
一个BI系统，一般应该有多个场景，每个场景对应一个业务，所以请把最重要的场景做为默认场景场景，请把默认场景生成的模板文件名称添加_default后缀，例如，demo_default.xlsx

### 第二步，请打开生成的提示词模板文件，进行审核，调整和修改
*建议审核的人应该是对当前场景业务非常数据的业务同事或数据同事，而非技术同事*

### 第三步，生成提示词
```
python3 prompt_gen.py prompt
```
这一步操作，会生成json格式的提示词文件，位于
```
prompt/prompt_conf 文件夹下
```
并且会把该文件上传到环境变量中指定的桶
例如，你配置的
BUCKET_NAME=tx-text2sql2

EXAMPLE_FILE_NAME=demo/defaultDragonPrompt.json
PROMPT_FILE_NAME=demo/promptConfig.json
RAG_FILE_NAME=demo/ragSampleList.json
则会上传到
s3://tx-text2sql2/demo/defaultDragonPrompt.json

注意：
EXAMPLE_FILE_NAME=demo/defaultDragonPrompt.json
保存的是常见问题的，多用户共享的问题，你可以先手动修改后再调用 python3 prompt_gen.py prompt

### 第四步，重启服务
如果修改了各个场景的提示词，只需要重启后端
如果修改了defaultDragonPrompt.json, 则需要重启前端


## 自动调优提示词
*还在开发中*
基于multiple agent，限定好优化准则，实现，参考
参考的内容1：https://arxiv.org/abs/2304.11015。 （或者附件1）。主要讲模式链接（Schema Linking）、查询分类与分解（Query Classification and Decomposition）、SQL生成（SQL Generation）和自我修正（Self-Correction）几种提示词方法来增加准确率。

参考内容2：https://arxiv.org/abs/2211.01910。（或者附件2）。主要讲通过大模型，对一个任务生成多候选prompt集合，再根据一些sample来挑选最合适的prompt来提高prompt的效果。
（https://zhuanlan.zhihu.com/p/672206721）。

### 前置条件，需要你编测试样例
测试样例参考
```
/server/testcases/sql_testcase1.xlsx
```











