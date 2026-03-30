import mysql.connector
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'learning_platform',
    'port': 3306
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    backup_file = open('learning_platform_backup.sql', 'w', encoding='utf-8')
    backup_file.write(f"-- MySQL Database Backup\n")
    backup_file.write(f"-- Database: learning_platform\n")
    backup_file.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    for table in tables:
        table_name = table[0]
        backup_file.write(f"\n-- Table: {table_name}\n")
        
        cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
        create_table = cursor.fetchone()[1]
        backup_file.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
        backup_file.write(f"{create_table};\n\n")
        
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        
        if rows:
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            
            for row in rows:
                values = []
                for val in row:
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        val_str = str(val).replace("'", "''")
                        values.append(f"'{val_str}'")
                
                backup_file.write(f"INSERT INTO `{table_name}` ({', '.join([f'`{c}`' for c in columns])}) VALUES ({', '.join(values)});\n")
    
    backup_file.close()
    cursor.close()
    conn.close()
    
    print(f'✅ 数据库备份成功: learning_platform_backup.sql')
    print(f'   表数量: {len(tables)}')
    
except Exception as e:
    print(f'❌ 数据库备份失败: {e}')
