import os
import json
import mysql.connector
from datetime import datetime
from typing import List, Dict, Optional, Any

class MySQLDatabase:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.get_connection()
        self.create_tables()
    
    def get_connection(self):
        try:
            if self.conn and self.conn.is_connected():
                return self.conn
            
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print(f'✅ 成功连接到MySQL数据库: {self.database}')
            return self.conn
        except Exception as e:
            print(f'❌ 连接MySQL数据库失败: {e}')
            self.conn = None
            return None
    
    def create_tables(self):
        conn = self.get_connection()
        if not conn:
            return
        
        tables = {
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
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
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    teacher_id INT,
                    category VARCHAR(100),
                    cover VARCHAR(255),
                    status VARCHAR(50),
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'chapters': '''
                CREATE TABLE IF NOT EXISTS chapters (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT,
                    title VARCHAR(255) NOT NULL,
                    order_index INT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'lessons': '''
                CREATE TABLE IF NOT EXISTS lessons (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    chapter_id INT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    content TEXT,
                    content_type VARCHAR(50),
                    content_path VARCHAR(255),
                    duration VARCHAR(50),
                    order_index INT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'learning_progress': '''
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    course_id INT,
                    chapter_id INT,
                    lesson_id INT,
                    progress INT,
                    completed TINYINT(1),
                    updated_at DATETIME
                )
            ''',
            'materials': '''
                CREATE TABLE IF NOT EXISTS materials (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT,
                    title VARCHAR(255) NOT NULL,
                    file_url VARCHAR(255),
                    type VARCHAR(50),
                    uploader_id INT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'discussions': '''
                CREATE TABLE IF NOT EXISTS discussions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT,
                    user_id INT,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    images TEXT,
                    category VARCHAR(100),
                    tags TEXT,
                    view_count INT DEFAULT 0,
                    like_count INT DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'replies': '''
                CREATE TABLE IF NOT EXISTS replies (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    discussion_id INT,
                    user_id INT,
                    parent_id INT,
                    content TEXT NOT NULL,
                    like_count INT DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'discussion_likes': '''
                CREATE TABLE IF NOT EXISTS discussion_likes (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    discussion_id INT,
                    user_id INT,
                    created_at DATETIME
                )
            ''',
            'reply_likes': '''
                CREATE TABLE IF NOT EXISTS reply_likes (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    reply_id INT,
                    user_id INT,
                    created_at DATETIME
                )
            ''',
            'code_shares': '''
                CREATE TABLE IF NOT EXISTS code_shares (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    title VARCHAR(255) NOT NULL,
                    code TEXT,
                    description TEXT,
                    language VARCHAR(50),
                    tags TEXT,
                    view_count INT,
                    like_count INT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'reviews': '''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT,
                    user_id INT,
                    rating INT,
                    comment TEXT,
                    created_at DATETIME
                )
            ''',
            'problem_categories': '''
                CREATE TABLE IF NOT EXISTS problem_categories (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    parent_id INT,
                    description TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'problems': '''
                CREATE TABLE IF NOT EXISTS problems (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    input_format TEXT,
                    output_format TEXT,
                    sample_input TEXT,
                    sample_output TEXT,
                    difficulty VARCHAR(50),
                    category_id INT,
                    time_limit INT,
                    memory_limit INT,
                    test_cases TEXT,
                    source VARCHAR(100),
                    source_id VARCHAR(100),
                    source_url VARCHAR(500),
                    is_public TINYINT(1) DEFAULT 0,
                    tags VARCHAR(500),
                    hint TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'submissions': '''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    problem_id INT,
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
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    problem_id INT,
                    question TEXT,
                    answer TEXT,
                    model_name VARCHAR(100),
                    conversation_type VARCHAR(100),
                    has_code TINYINT(1),
                    has_image TINYINT(1),
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''',
            'teacher_assignments': '''
                CREATE TABLE IF NOT EXISTS teacher_assignments (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    teacher_id INT,
                    problem_id INT,
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
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    teacher_id INT NOT NULL,
                    problem_id INT NOT NULL,
                    course_id INT,
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
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    admin_id INT NOT NULL,
                    source VARCHAR(100),
                    count INT,
                    status VARCHAR(50),
                    error_message TEXT,
                    created_at DATETIME
                )
            ''',
            'caigpt_dialog_history': '''
                CREATE TABLE IF NOT EXISTS caigpt_dialog_history (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = cursor.fetchall()
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            return rows
        except Exception as e:
            print(f'❌ 读取表 {table_name} 时出错: {e}')
            return []
    
    def write_table(self, table_name: str, data: List[Dict[str, Any]]):
        # MySQL通过insert方法直接操作，不需要write_table
        pass
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            # 准备插入数据
            if 'created_at' not in data:
                data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'updated_at' not in data:
                data['updated_at'] = data['created_at']
            
            # 构建SQL语句
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ','.join(['%s'] * len(values))
            
            sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            # 获取自增ID
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
            # 确保updated_at字段
            if 'updated_at' not in data:
                data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 构建SQL语句
            set_clause = ','.join([f"{key}=%s" for key in data.keys()])
            values = list(data.values())
            values.append(record_id)
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE id=%s"
            
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
            sql = f"DELETE FROM {table_name} WHERE id=%s"
            
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
            sql = f"SELECT * FROM {table_name} WHERE id=%s"
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (record_id,))
            row = cursor.fetchone()
            if row:
                print(f'✅ 找到 {table_name} 记录，ID: {record_id}')
                cursor.close()
                return self._convert_datetime_to_string(row)
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
            # 构建SQL语句，使用精确匹配
            sql = f"SELECT * FROM {table_name} WHERE {field_name} = %s"
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (field_value,))
            rows = cursor.fetchall()
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
                where_clause = ' WHERE ' + ' AND '.join([f"{key}=%s" for key in filters.keys()])
                values = list(filters.values())
                sql = f"SELECT * FROM {table_name}{where_clause}"
            else:
                sql = f"SELECT * FROM {table_name}"
                values = []
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, values)
            rows = cursor.fetchall()
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
                where_clause = ' WHERE ' + ' AND '.join([f"{key}=%s" for key in filters.keys()])
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