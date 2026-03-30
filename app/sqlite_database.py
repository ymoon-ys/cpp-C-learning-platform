import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

class SQLiteDatabase:
    def __init__(self, database_path):
        self.database_path = database_path
        self.conn = None
        try:
            self.get_connection()
            if self.conn:
                self.create_tables()
        except Exception as e:
            print(f'❌ 数据库初始化失败: {e}')
    
    def get_connection(self):
        try:
            if self.conn:
                try:
                    self.conn.execute('SELECT 1')
                    return self.conn
                except:
                    self.conn.close()
                    self.conn = None
            
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row
            print(f'✅ 成功连接到SQLite数据库: {self.database_path}')
            return self.conn
        except Exception as e:
            print(f'❌ 连接SQLite数据库失败: {e}')
            self.conn = None
            return None
    
    def create_tables(self):
        conn = self.get_connection()
        if not conn:
            return
        
        tables = {
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    nickname VARCHAR(255),
                    avatar VARCHAR(255),
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'courses': '''
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    teacher_id INTEGER,
                    category VARCHAR(100),
                    cover VARCHAR(255),
                    status VARCHAR(50),
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'chapters': '''
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    order_index INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'lessons': '''
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    content TEXT,
                    content_type VARCHAR(50),
                    content_path VARCHAR(255),
                    duration VARCHAR(50),
                    order_index INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'learning_progress': '''
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    course_id INTEGER,
                    chapter_id INTEGER,
                    lesson_id INTEGER,
                    progress INTEGER,
                    completed INTEGER DEFAULT 0,
                    updated_at DATETIME
                )
            ''',
            'materials': '''
                CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    file_url VARCHAR(255),
                    type VARCHAR(50),
                    uploader_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'discussions': '''
                CREATE TABLE IF NOT EXISTS discussions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    user_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    images TEXT,
                    category VARCHAR(100),
                    tags TEXT,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'replies': '''
                CREATE TABLE IF NOT EXISTS replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discussion_id INTEGER,
                    user_id INTEGER,
                    parent_id INTEGER,
                    content TEXT NOT NULL,
                    like_count INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'discussion_likes': '''
                CREATE TABLE IF NOT EXISTS discussion_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discussion_id INTEGER,
                    user_id INTEGER,
                    created_at DATETIME
                )
            ''',
            'reply_likes': '''
                CREATE TABLE IF NOT EXISTS reply_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reply_id INTEGER,
                    user_id INTEGER,
                    created_at DATETIME
                )
            ''',
            'code_shares': '''
                CREATE TABLE IF NOT EXISTS code_shares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    code TEXT,
                    description TEXT,
                    language VARCHAR(50),
                    tags TEXT,
                    view_count INTEGER,
                    like_count INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'reviews': '''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    created_at DATETIME
                )
            ''',
            'problem_categories': '''
                CREATE TABLE IF NOT EXISTS problem_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    parent_id INTEGER,
                    description TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'problems': '''
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    input_format TEXT,
                    output_format TEXT,
                    sample_input TEXT,
                    sample_output TEXT,
                    difficulty VARCHAR(50),
                    category_id INTEGER,
                    time_limit INTEGER,
                    memory_limit INTEGER,
                    test_cases TEXT,
                    source VARCHAR(100),
                    source_id VARCHAR(100),
                    source_url VARCHAR(500),
                    is_public INTEGER DEFAULT 0,
                    tags VARCHAR(500),
                    hint TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'submissions': '''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    problem_id INTEGER,
                    code TEXT NOT NULL,
                    status VARCHAR(50),
                    error_message TEXT,
                    submit_time DATETIME,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'ai_conversations': '''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    problem_id INTEGER,
                    question TEXT,
                    answer TEXT,
                    model_name VARCHAR(100),
                    conversation_type VARCHAR(100),
                    has_code INTEGER DEFAULT 0,
                    has_image INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'teacher_assignments': '''
                CREATE TABLE IF NOT EXISTS teacher_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER,
                    problem_id INTEGER,
                    title VARCHAR(255),
                    description TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'teacher_selected_problems': '''
                CREATE TABLE IF NOT EXISTS teacher_selected_problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    problem_id INTEGER NOT NULL,
                    course_id INTEGER,
                    selected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    visible_start DATETIME,
                    visible_end DATETIME,
                    notes TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'problem_import_logs': '''
                CREATE TABLE IF NOT EXISTS problem_import_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    source VARCHAR(100),
                    count INTEGER,
                    status VARCHAR(50),
                    error_message TEXT,
                    created_at DATETIME
                )
            ''',
            'caigpt_dialog_history': '''
                CREATE TABLE IF NOT EXISTS caigpt_dialog_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    images TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
        }
        
        cursor = conn.cursor()
        for table_name, create_sql in tables.items():
            try:
                cursor.execute(create_sql)
                conn.commit()
                print(f'✅ 成功创建表: {table_name}')
            except Exception as e:
                print(f'❌ 创建表 {table_name} 时出错: {e}')
        cursor.close()
    
    def _convert_datetime_to_string(self, row: Dict[str, Any]) -> Dict[str, Any]:
        if not row:
            return row
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        return row
    
    def read_table(self, table_name: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            return rows
        except Exception as e:
            print(f'❌ 读取表 {table_name} 时出错: {e}')
            return []
    
    def write_table(self, table_name: str, data: List[Dict[str, Any]]):
        pass
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            if 'created_at' not in data:
                data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'updated_at' not in data:
                data['updated_at'] = data['created_at']
            
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ','.join(['?'] * len(values))
            
            sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            print(f'✅ 成功插入 {table_name} 记录，ID: {new_id}')
            return new_id
        except Exception as e:
            print(f'❌ 插入 {table_name} 记录时出错: {e}')
            return 0
    
    def update(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            if 'updated_at' not in data:
                data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            set_clause = ','.join([f"{key}=?" for key in data.keys()])
            values = list(data.values())
            values.append(record_id)
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE id=?"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount > 0:
                print(f'✅ 成功更新 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return True
            else:
                print(f'❌ 未找到 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return False
        except Exception as e:
            print(f'❌ 更新 {table_name} 记录时出错: {e}')
            return False
    
    def delete(self, table_name: str, record_id: int) -> bool:
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            sql = f"DELETE FROM {table_name} WHERE id=?"
            
            cursor = conn.cursor()
            cursor.execute(sql, (record_id,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f'✅ 成功删除 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return True
            else:
                print(f'❌ 未找到 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return False
        except Exception as e:
            print(f'❌ 删除 {table_name} 记录时出错: {e}')
            return False
    
    def find_by_id(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            sql = f"SELECT * FROM {table_name} WHERE id=?"
            
            cursor = conn.cursor()
            cursor.execute(sql, (record_id,))
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                print(f'✅ 找到 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return self._convert_datetime_to_string(row_dict)
            else:
                print(f'❌ 未找到 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return None
        except Exception as e:
            print(f'❌ 查找 {table_name} 记录时出错: {e}')
            return None
    
    def find_by_field(self, table_name: str, field_name: str, field_value: Any) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            sql = f"SELECT * FROM {table_name} WHERE {field_name} = ?"
            
            cursor = conn.cursor()
            cursor.execute(sql, (field_value,))
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            print(f'✅ 找到 {len(rows)} 条 {table_name} 记录，字段: {field_name}, 值: {field_value}')
            return rows
        except Exception as e:
            print(f'❌ 查找 {table_name} 记录时出错: {e}')
            return []
    
    def find_all(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            if filters:
                where_clause = ' WHERE ' + ' AND '.join([f"{key}=?" for key in filters.keys()])
                values = list(filters.values())
                sql = f"SELECT * FROM {table_name}{where_clause}"
            else:
                sql = f"SELECT * FROM {table_name}"
                values = []
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            return rows
        except Exception as e:
            print(f'❌ 查找 {table_name} 记录时出错: {e}')
            return []
    
    def count(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            if filters:
                where_clause = ' WHERE ' + ' AND '.join([f"{key}=?" for key in filters.keys()])
                values = list(filters.values())
                sql = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
            else:
                sql = f"SELECT COUNT(*) FROM {table_name}"
                values = []
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            print(f'❌ 统计 {table_name} 记录时出错: {e}')
            return 0
    
    def find_by_ids(self, table_name: str, ids: List[int]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            placeholders = ','.join(['?'] * len(ids))
            sql = f"SELECT * FROM {table_name} WHERE id IN ({placeholders})"
            
            cursor = conn.cursor()
            cursor.execute(sql, ids)
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            return rows
        except Exception as e:
            print(f'❌ 批量查询 {table_name} 记录时出错: {e}')
            return []
    
    def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> int:
        if not data_list:
            return 0
        
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            columns = list(data_list[0].keys())
            placeholders = ','.join(['?'] * len(columns))
            sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            for data in data_list:
                values = [data.get(col) for col in columns]
                cursor.execute(sql, values)
            
            conn.commit()
            inserted_count = cursor.rowcount
            cursor.close()
            print(f'✅ 批量插入 {table_name} 记录: {inserted_count} 条')
            return inserted_count
        except Exception as e:
            print(f'❌ 批量插入 {table_name} 记录时出错: {e}')
            return 0