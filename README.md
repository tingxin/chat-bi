
# 使用Bedrock 构建生成式BI
*代码原型使用aws rp团队*
![图示](assets/demo1.jpg)
## 快速体验
docker build -t text2sql .

docker run --env-file=.env -p 5017:8900  --name textdemo1 text2sql

使用浏览器打开
ip:5017



## 如何配置数据
1. 进入prompt文件夹
2. 参考README.md文件配置数据
3. 重新运行docker 
