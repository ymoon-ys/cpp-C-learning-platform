import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

def export_local_data():
    local_conn = pymysql.connect(
        host='localhost',
        user='root',
        password='ccy20070626',
        database='learning_platform',
        charset='utf8mb4'
    )
    
    tables_data = {}
    tables_order = ['users', 'courses', 'chapters', 'lessons', 'enrollments', 
                   'progress', 'questions', 'submissions', 'resources', 'announcements']
    
    cursor = local_conn.cursor()
    
    for table in tables_order:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if rows:
                cursor.execute(f"DESCRIBE {table}")
                columns = [col[0] for col in cursor.fetchall()]
                tables_data[table] = {'columns': columns, 'rows': rows}
                print(f"导出 {table}: {len(rows)} 条记录")
        except Exception as e:
            print(f"跳过表 {table}: {e}")
    
    cursor.execute("SHOW TABLES")
    all_tables = [t[0] for t in cursor.fetchall()]
    
    for table in all_tables:
        if table not in tables_data:
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                if rows:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = [col[0] for col in cursor.fetchall()]
                    tables_data[table] = {'columns': columns, 'rows': rows}
                    print(f"导出 {table}: {len(rows)} 条记录")
            except Exception as e:
                print(f"跳过表 {table}: {e}")
    
    local_conn.close()
    return tables_data

def import_to_aiven(tables_data, aiven_config):
    print(f"\n连接到 Aiven MySQL: {aiven_config['host']}:{aiven_config['port']}")
    
    aiven_conn = pymysql.connect(
        host=aiven_config['host'],
        user=aiven_config['user'],
        password=aiven_config['password'],
        database=aiven_config['database'],
        port=aiven_config['port'],
        charset='utf8mb4',
        ssl={'ssl_ca': None}
    )
    
    cursor = aiven_conn.cursor()
    
    for table, data in tables_data.items():
        columns = data['columns']
        rows = data['rows']
        
        if not rows:
            continue
        
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        try:
            cursor.executemany(sql, rows)
            aiven_conn.commit()
            print(f"导入 {table}: {len(rows)} 条记录 ✓")
        except Exception as e:
            print(f"导入 {table} 失败: {e}")
            aiven_conn.rollback()
    
    aiven_conn.close()
    print("\n导入完成!")

if __name__ == '__main__':
    print("=" * 50)
    print("从本地 MySQL 导出数据")
    print("=" * 50)
    
    tables_data = export_local_data()
    
    if not tables_data:
        print("没有数据需要导出!")
        sys.exit(0)
    
    print(f"\n共导出 {len(tables_data)} 个表的数据")
    
    print("\n使用 Aiven MySQL 连接信息:")
    aiven_config = {
        'host': 'mysql-3c6bff41-project-4c37.j.aivencloud.com',
        'port': 12581,
        'user': 'avnadmin',
        'password': '[Aiven MySQL 密码]',
        'database': 'defaultdb'
    }
    
    print(f"主机: {aiven_config['host']}")
    print(f"端口: {aiven_config['port']}")
    print(f"用户名: {aiven_config['user']}")
    print(f"数据库: {aiven_config['database']}")
    
    import_to_aiven(tables_data, aiven_config)
