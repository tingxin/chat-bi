
# ChatBI
![图示](assets/demo1.jpg)
快速构建会话是BI工具，帮助非专业人员探索分析数据
## 优势
1. 支持MySQL、StarRocks、 Doris, Hive 等多种数据库及数据仓库
2. 无需提示词工程经验，即可构建生成式BI系统

## 主要功能
1. 使用自然语言查询数据，并生成图表
2. 自动生成提示词，并使用Multiple Agent技术对提示词进行优化，提高查询准确性
3. 支持自定义SQL模板，解决复杂SQL的生成问题
4. 支持联邦查询功能，可以从多个数据源联合查询，服务端进行合并
5. 支持代理部署模式，数据查询服务和模型推理服务分离部署

*代码原型使用aws rp团队*


## 架构

项目使用Multiple Agent 构建提示词模板，提高查询准确性。提示词模板是对被查询数据的描述，用于让大模型理解数据的含义，从而回应用户的查询
![提示词优化](assets/chatbi-prompt.drawio.png)
1. Prompt Engineer Agent 从源库获取涉及的表的元信息和采样数据，经过分析后生成提示词模板
2. Data Engineer Agent 使用上个步骤产生的提示词模板，和测试问题集合，生成SQL,并执行获取返回的结果
3. Test Engineer Agent 根据用户提供的测试问题集的信息，和上个步骤返回的数据，评判生成SQL的质量，生成反馈
4. Prompt Engineer Agent 根据反馈重新生成提示词模板，进入下一轮迭代优化
5. 最终生成的最优提示词模板被做为实际推理的提示词上下文

项目整体架构如下
![系统架构](assets/arch.png)
1. 用户发起请求后，用户问题进行embedding 
## 快速体验
1. 配置环境变量
进入.env文件，根据注释提供aws ak, sk等信息


# 如果在中国区，请手动执行
```
git clone -b v1.7.4 --depth 1 https://github.com/facebookresearch/faiss.git deps/faiss
```
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


## 配置本地文件下载
默认情况下，数据文件会上传到s3,提供下载，如果你希望使用服务器做为下载服务，避免使用公网访问s3客户如下配置
创建一个downloads文件夹
```
mkdir downloads
cd downloads
```

创建一个简单的文件服务器,例如
```
python3 -m http.server 端口号

python3 -m http.server 5023
```

进入环境变量文件.env，添加环境变量
```
DOWNLOAD_HOST={文件服务器的公网或内网IP}:端口
```



## 如何配置数据
1. 进入prompt文件夹
2. 参考README.md文件配置数据
3. 重新运行docker 



