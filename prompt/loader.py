import pandas as pd
import os
import json
from pysqler import Insert

def load_from_excel(doc_path, table_name, conn, sheet_index=0,):
    df = pd.read_excel(doc_path, sheet_name=sheet_index)
    
    # 数据表格第一行不是真正的列
    df.columns = df.iloc[0]
    print(df.columns)
    df = df.drop(df.index[0])
    df.reset_index(drop=True, inplace=True)
    ##########################################

    for i in range(0, len(df)):
        command = Insert("`{0}`".format(table_name))
        for column_name in df.columns:
            v = df.loc[i, column_name]
            if not pd.isna(v):
                command.put(column_name, df.loc[i, column_name])
            else:
                command.put(column_name, None)

        sql = str(command)
        with conn.cursor() as cursor:
            sql = str(command)
            cursor.execute(sql)
            conn.commit()
        
        
        
