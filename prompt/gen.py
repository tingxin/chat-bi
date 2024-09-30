from ..server.db import mysql
from ..server.api_helpler import Helper
from ..server import conf

dbinfo = conf.get_mysql_conf(db_key="default")

SHOW_SCHEMA_F = """
SHOW FULL COLUMNS FROM {0};
"""


def get_tables_schema(tables_name:list):
    scenarios = dict()
    for tb_name in tables_name:
        tsql =SHOW_SCHEMA_F.format(tb_name) 
        db_result = Helper.query_db(dbinfo, tsql, "default_user", "default_request")
        rows = db_result["rows"]
        schema = list()

        for row in rows:
            field = dict()
            field['Name'] = row[0]
            field['Type'] = row[1]
            field['Key'] = row[4]
            field['Comment'] = row[8]
            schema.append(field)

        scenarios[tb_name] = schema



def get_sample_data(table_name:str, schema:dict):
    sql = list()
    sql.append("SELECT")
    columns = list()
    for row in schema:
        columns.append(f"distnct {row['Name']}")

    column_str = ','.join(columns)
    sql = f"SELECT {column_str} FROM {table_name} LIMIT 10"




