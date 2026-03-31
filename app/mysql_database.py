import os
import json
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
from typing import List, Dict, Optional, Any
import threading
import time

class MySQLDatabase:
    _connection_pool = None
    _pool_lock = threading.Lock()
    
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = None
        
        if MySQLDatabase._connection_pool is None:
            with MySQLDatabase._pool_lock:
                if MySQLDatabase._connection_pool is None:
                    self._create_pool_with_retry()
        
        try:
            self.get_connection()
            if self.conn:
                self.create_tables()
        except Exception as e:
            print(f'[ERR] Database initialization failed: {e}')
    
    def _create_pool_with_retry(self, max_retries=3, retry_delay=2):
        for attempt in range(max_retries):
            try:
                MySQLDatabase._connection_pool = pooling.MySQLConnectionPool(
                    pool_name='learning_platform_pool',
                    pool_size=5,
                    pool_reset_session=True,
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    port=self.port,
                    autocommit=True
                )
                print(f'[OK] Database connection pool created successfully')
                return True
            except Exception as e:
                print(f'[ERR] Failed to create connection pool (attempt {attempt + 1}/{max_retries}): {e}')
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        MySQLDatabase._connection_pool = None
        return False
    
    def get_connection(self):
        try:
            if self.conn and self.conn.is_connected():
                return self.conn
            
            if MySQLDatabase._connection_pool:
                try:
                    self.conn = MySQLDatabase._connection_pool.get_connection()
                    print(f'[OK] Got database connection from pool')
                    return self.conn
                except Exception as e:
                    print(f'[WARN] Failed to get connection from pool, creating new: {e}')
            
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                autocommit=True
            )
            print(f'[OK] Connected to MySQL database: {self.database}')
            return self.conn
        except Exception as e:
            print(f'[ERR] Failed to connect to MySQL database: {e}')
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
                print(f'[OK] Table created: {table_name}')
            except Exception as e:
                print(f'[ERR] Error creating table {table_name}: {e}')
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
            print(f'[ERR] Error reading table {table_name}: {e}')
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
            placeholders = ','.join(['%s'] * len(values))
            
            sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            print(f'[OK] Inserted {table_name} record, ID: {new_id}')
            return new_id
        except Exception as e:
            print(f'[ERR] Error inserting {table_name} record: {e}')
            return 0
    
    def update(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            if 'updated_at' not in data:
                data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            set_clause = ','.join([f"{key}=%s" for key in data.keys()])
            values = list(data.values())
            values.append(record_id)
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE id=%s"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount > 0:
                print(f'[OK] Updated {table_name} record, ID: {record_id}')
                cursor.close()
                return True
            else:
                print(f'[ERR] {table_name} record not found, ID: {record_id}')
                cursor.close()
                return False
        except Exception as e:
            print(f'[ERR] Error updating {table_name} record: {e}')
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
                print(f'[OK] Deleted {table_name} record, ID: {record_id}')
                cursor.close()
                return True
            else:
                print(f'[ERR] {table_name} record not found, ID: {record_id}')
                cursor.close()
                return False
        except Exception as e:
            print(f'[ERR] Error deleting {table_name} record: {e}')
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
                print(f'[OK] Found {table_name} record, ID: {record_id}')
                cursor.close()
                return self._convert_datetime_to_string(row)
            else:
                print(f'[ERR] {table_name} record not found, ID: {record_id}')
                cursor.close()
                return None
        except Exception as e:
            print(f'[ERR] Error finding {table_name} record: {e}')
            return None
    
    def find_by_field(self, table_name: str, field_name: str, field_value: Any) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            sql = f"SELECT * FROM {table_name} WHERE {field_name} = %s"
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (field_value,))
            rows = cursor.fetchall()
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            print(f'[OK] Found {len(rows)} {table_name} records, field: {field_name}, value: {field_value}')
            return rows
        except Exception as e:
            print(f'[ERR] Error finding {table_name} records: {e}')
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
            print(f'[ERR] Error finding {table_name} records: {e}')
            return []
    
    def count(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        conn = self.get_connection()
        if not conn:
            return -1
        
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
            print(f'[ERR] Error counting {table_name} records: {e}')
            return -1
    
    def find_by_ids(self, table_name: str, ids: List[int]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            placeholders = ','.join(['%s'] * len(ids))
            sql = f"SELECT * FROM {table_name} WHERE id IN ({placeholders})"
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, ids)
            rows = cursor.fetchall()
            cursor.close()
            for i, row in enumerate(rows):
                rows[i] = self._convert_datetime_to_string(row)
            return rows
        except Exception as e:
            print(f'[ERR] Error batch querying {table_name} records: {e}')
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
            placeholders = ','.join(['%s'] * len(columns))
            sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            for data in data_list:
                values = [data.get(col) for col in columns]
                cursor.execute(sql, values)
            
            conn.commit()
            inserted_count = cursor.rowcount
            cursor.close()
            print(f'[OK] Batch inserted {table_name} records: {inserted_count}')
            return inserted_count
        except Exception as e:
            print(f'[ERR] Error batch inserting {table_name} records: {e}')
            return 0
