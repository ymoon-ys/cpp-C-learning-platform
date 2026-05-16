import os
import mysql.connector
from mysql.connector import Error

class MySQLConnector:
    def __init__(self, host=None, user=None, password=None, database=None, port=3306):
        self.host = host or os.getenv('MYSQL_HOST', 'localhost')
        self.user = user or os.getenv('MYSQL_USER', 'root')
        self.password = password or os.getenv('MYSQL_PASSWORD', '')
        self.database = database or os.getenv('MYSQL_DATABASE', '')
        self.port = port
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                print(f'✓ 成功连接到MySQL数据库: {self.database}')
                return True
        except Error as e:
            print(f'✗ 连接数据库失败: {e}')
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print('✓ 已断开数据库连接')

    def execute_query(self, query, params=None, fetch=True):
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None

        try:
            self.cursor = self.connection.cursor(dictionary=True)
            self.cursor.execute(query, params or ())

            if fetch:
                result = self.cursor.fetchall()
                return result
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Error as e:
            print(f'✗ 执行查询失败: {e}')
            return None

    def get_tables(self):
        return self.execute_query('SHOW TABLES')

    def describe_table(self, table_name):
        return self.execute_query(f'DESCRIBE {table_name}')

    def select_all(self, table_name, limit=100):
        return self.execute_query(f'SELECT * FROM {table_name} LIMIT {limit}')

    def insert(self, table_name, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        return self.execute_query(query, tuple(data.values()), fetch=False)

    def update(self, table_name, data, condition):
        set_clause = ', '.join([f'{k} = %s' for k in data.keys()])
        query = f'UPDATE {table_name} SET {set_clause} WHERE {condition}'
        params = tuple(data.values())
        return self.execute_query(query, params, fetch=False)

    def delete(self, table_name, condition):
        query = f'DELETE FROM {table_name} WHERE {condition}'
        return self.execute_query(query, fetch=False)


def main():
    print('=' * 60)
    print('MySQL数据库连接工具')
    print('=' * 60)

    host = input('\n请输入MySQL主机 [localhost]: ').strip() or 'localhost'
    port = input('请输入端口 [3306]: ').strip() or '3306'
    user = input('请输入用户名 [root]: ').strip() or 'root'
    password = input('请输入密码: ').strip()
    database = input('请输入数据库名: ').strip()

    print()

    db = MySQLConnector(
        host=host,
        user=user,
        password=password,
        database=database,
        port=int(port)
    )

    if db.connect():
        print()
        print('可用命令:')
        print('  1. 查看所有表')
        print('  2. 查看表结构')
        print('  3. 查询表数据')
        print('  4. 退出')
        print()

        while True:
            choice = input('请选择操作 [4]: ').strip() or '4'

            if choice == '1':
                tables = db.get_tables()
                if tables:
                    print(f'\n数据库 {database} 中的表:')
                    for i, table in enumerate(tables, 1):
                        table_name = list(table.values())[0]
                        print(f'  {i}. {table_name}')

            elif choice == '2':
                table_name = input('请输入表名: ').strip()
                if table_name:
                    structure = db.describe_table(table_name)
                    if structure:
                        print(f'\n表 {table_name} 的结构:')
                        for row in structure:
                            print(f'  {row}')

            elif choice == '3':
                table_name = input('请输入表名: ').strip()
                if table_name:
                    data = db.select_all(table_name)
                    if data:
                        print(f'\n表 {table_name} 的数据 (前100条):')
                        for row in data:
                            print(f'  {row}')
                    else:
                        print('表为空或不存在')

            elif choice == '4':
                break

            print()

        db.disconnect()
    else:
        print('无法连接到数据库')


if __name__ == '__main__':
    main()