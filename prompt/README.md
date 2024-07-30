
## prompt
生成prompt提示词文件

### 前提
1. 安装依赖
```
pip install -r requirement.txt

```

2. 参考prompt/data文件下的rawdata.xlsx，描述你的数据



3. 修改app.py代码中的 Scenario 字典对象

### 使用
1. 生成提示词
```
python3 app.py
```
2. 生成的提示词文件在prompt_conf文件夹下。

3. 查看根目录下的.env文件，将生成的提示词文件放入.env文件中指定的s3 bucket






