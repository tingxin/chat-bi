import os

mysql_info = dict()

# 定义一个函数来加载.env文件
def load_env(filename='.env'):
    # 确保.env文件存在
    if not os.path.exists(filename):
        raise FileNotFoundError(f"The specified file {filename} was not found.")

    # 读取.env文件中的每行
    with open(filename, 'r') as file:
        for line in file:
            # 忽略注释和空行
            line = line.strip()
            if line and not line.startswith('#'):
                # 分割键和值
                key_value_pair = line.split('=', 1)
                if len(key_value_pair) == 2:
                    key, value = key_value_pair
                    # 将键值对设置为环境变量
                    os.environ[key] = value

def get_env(key:str, default_v:str):
    return os.getenv(key, default_v)

def get_mysql_conf(db_key:str='au'):
    if len(mysql_info) == 0:
        hosts = os.getenv("MYSQL_HOST").split(",")
        databases = os.getenv("MYSQL_DATABASE").split(",")
        users = os.getenv("MYSQL_USER").split(",")
        pwds = os.getenv("MYSQL_PWD").split(",")
        keys = os.getenv("MYSQL_KEY").split(",")



        for index in range(0, len(keys)):
            mysql_info[keys[index]] = {
                "host":hosts[index],
                "db":databases[index],
                "user":users[index],
                "pwd":pwds[index]
            }

    if db_key in mysql_info:
        return mysql_info[db_key]

    return ValueError(f"db key {db_key} not found")

    
