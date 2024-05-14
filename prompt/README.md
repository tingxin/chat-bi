
## prompt
生成prompt提示词文件

### 前提
1. 安装依赖
```
pip install -r requirement.txt

```
2. 按照约定的数据格式，把数据文件放在data文件夹下


3. 修改app.py代码中的 Scenario 字典对象

### 使用
1. 生成提示词
```
python3 app.py
```
生成的提示词文件在prompt_conf文件夹下

2. 讲提示词文件全部放入约定好的s3 bucket中 （sungrow-text2sql-prompt）





