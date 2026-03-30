"""
SQLite 到 MySQL 数据迁移脚本
"""
import sqlite3
import mysql.connector
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class DatabaseMigrator:
    def __init__(self, sqlite_path, mysql_config):
        self.sqlite_path = sqlite_path
        self.mysql_config = mysql_config
        self.sqlite_conn = None
        self.mysql_conn = None
        
    def connect_sqlite(self):
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            print(f'✅ 成功连接到SQLite数据库: {self.sqlite_path}')
            return True
        except Exception as e:
            print(f'❌ 连接SQLite失败: {e}')
            return False
    
    def connect_mysql(self):
        try:
            self.mysql_conn = mysql.connector.connect(**self.mysql_config)
            print(f'✅ 成功连接到MySQL数据库: {self.mysql_config["database"]}')
            return True
        except Exception as e:
            print(f'❌ 连接MySQL失败: {e}')
            return False
    
    def get_sqlite_tables(self):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    def get_table_columns(self, table_name):
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        cursor.close()
        return columns
    
    def migrate_table(self, table_name):
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_mysql = self.mysql_conn.cursor()
        
        columns = self.get_table_columns(table_name)
        columns_str = ', '.join([f'`{col}`' for col in columns])
        placeholders = ', '.join(['%s'] * len(columns))
        
        cursor_sqlite.execute(f"SELECT * FROM {table_name}")
        rows = cursor_sqlite.fetchall()
        
        if not rows:
            print(f'  表 {table_name}: 无数据，跳过')
            return 0
        
        migrated = 0
        for row in rows:
            values = []
            for i, col in enumerate(columns):
                val = row[i]
                if val is None:
                    values.append(None)
                elif isinstance(val, bytes):
                    values.append(val.decode('utf-8', errors='ignore'))
                else:
                    values.append(val)
            
            try:
                sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                cursor_mysql.execute(sql, values)
                migrated += 1
            except mysql.connector.IntegrityError:
                pass
            except Exception as e:
                print(f'  警告: 插入记录失败 - {e}')
        
        self.mysql_conn.commit()
        cursor_sqlite.close()
        cursor_mysql.close()
        
        print(f'  表 {table_name}: 迁移 {migrated} 条记录')
        return migrated
    
    def migrate(self):
        print('\n=== 开始数据迁移 ===\n')
        
        if not self.connect_sqlite():
            return False
        
        if not self.connect_mysql():
            return False
        
        tables = self.get_sqlite_tables()
        print(f'\n发现 {len(tables)} 个表: {", ".join(tables)}\n')
        
        total_migrated = 0
        for table in tables:
            count = self.migrate_table(table)
            total_migrated += count
        
        print(f'\n=== 迁移完成 ===')
        print(f'总共迁移 {total_migrated} 条记录')
        
        self.sqlite_conn.close()
        self.mysql_conn.close()
        
        return True

def main():
    sqlite_path = 'database/learning_platform.db'
    
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', '123456'),
        'database': os.getenv('MYSQL_DATABASE', 'learning_platform'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'charset': 'utf8mb4'
    }
    
    print('MySQL连接配置:')
    print(f'  主机: {mysql_config["host"]}')
    print(f'  用户: {mysql_config["user"]}')
    print(f'  数据库: {mysql_config["database"]}')
    print(f'  端口: {mysql_config["port"]}')
    print()
    
    if not os.path.exists(sqlite_path):
        print(f'错误: SQLite数据库文件不存在: {sqlite_path}')
        sys.exit(1)
    
    migrator = DatabaseMigrator(sqlite_path, mysql_config)
    success = migrator.migrate()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
