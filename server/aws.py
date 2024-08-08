import boto3
import csv
import io
from datetime import datetime, timedelta
import os

def get(service_name:str):
    is_dev =bool(os.getenv('DEV_MODEL'))
    if service_name == 's3' and is_dev:
        client = boto3.client(
            service_name,
            region_name = os.getenv('DEFAULT_REGION')
        )
        return client
           

    if 'ACCESS_KEY' in os.environ and 'SECRET_ACCESS_KEY' in os.environ and len(os.environ['ACCESS_KEY']) == 20:
       return boto3.client(
            service_name,
            region_name = os.getenv('DEFAULT_REGION'),
            aws_access_key_id=os.getenv('ACCESS_KEY'),
            aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY')
       )

    return boto3.client(
            service_name,
            region_name = os.getenv('DEFAULT_REGION')
        )



def upload_csv_to_s3(columns, rows, bucket_name, file_name):
    # 创建一个S3客户端
    s3_client = get("s3")

    # 将数据写入CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入列名
    writer.writerow(columns)
    
    # 写入行数据
    for row in rows:
        items = [item for item in row]
        writer.writerow(items)
    
    # 获取CSV内容
    csv_content = output.getvalue()
    output.close()

    # 将CSV内容转换为字节串
    csv_bytes = csv_content.encode('utf-8')


    # 上传到S3
    
    now = datetime.now()

    # 格式化日期为 "YYYY-MM-DD" 格式
    formatted_date = now.strftime("%Y-%m-%d")
    s3_key = f"data/download/{formatted_date}/{file_name}.csv"
    try:
        s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=csv_bytes)
        print(f"文件已上传至 {bucket_name}/{s3_key}")
    except Exception as e:
        print(f"上传到s3错误：{e}")
        return None

    # 生成预签名URL
    try:
        expiration = datetime.now() + timedelta(minutes=10)  # URL过期时间
        presigned_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': bucket_name, 'Key': s3_key},
                                                         ExpiresIn=10*60)  # URL有效时间10分钟
        print(f"预签名URL: {presigned_url}")
        return presigned_url
    except Exception as e:
        print(f"生成预签名错误：{e}")
        return None

# 使用示例
columns = ['Column1', 'Column2', 'Column3']
rows = [
    [1, 'Data2', 'Data3'],
    [4, 'Data5', 'Data6'],
]

bucket_name = 'your-bucket-name'
s3_key = 'your/s3/key.csv'

url = upload_csv_to_s3(columns, rows, bucket_name, s3_key)
if url:
    print(f"文件上传成功，URL: {url}")
else:
    print("文件上传失败")