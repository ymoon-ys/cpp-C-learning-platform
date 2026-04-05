import os
import json
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
from typing import List, Dict, Optional, Any
import threading
import time

class MySQLDatabase:
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = None
        self._connection_pool = None
        
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
                self._connection_pool = pooling.MySQLConnectionPool(
                    pool_name=f'learning_platform_pool_{id(self)}',
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
        
        self._connection_pool = None
        return False
    
    def get_connection(self):
        try:
            if self.conn is not None:
                try:
                    if self.conn.is_connected():
                        return self.conn
                except Exception:
                    self.conn = None
            
            if self._connection_pool:
                try:
                    self.conn = self._connection_pool.get_connection()
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
                    role VARCHAR(50) NOT NULL DEFAULT 'student',
                    nickname VARCHAR(255),
                    avatar VARCHAR(500),
                    bio TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_username (username),
                    UNIQUE KEY uk_email (email),
                    KEY idx_role (role),
                    KEY idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表'
            ''',
            'courses': '''
                CREATE TABLE IF NOT EXISTS courses (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    teacher_id INT,
                    category VARCHAR(100),
                    cover VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'draft',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_teacher_id (teacher_id),
                    KEY idx_category (category),
                    KEY idx_status (status),
                    CONSTRAINT fk_courses_teacher FOREIGN KEY (teacher_id) REFERENCES users (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程表'
            ''',
            'chapters': '''
                CREATE TABLE IF NOT EXISTS chapters (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    order_index INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_course_id (course_id),
                    CONSTRAINT fk_chapters_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='章节表'
            ''',
            'lessons': '''
                CREATE TABLE IF NOT EXISTS lessons (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    chapter_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    content TEXT,
                    content_type VARCHAR(50) DEFAULT 'text',
                    content_path VARCHAR(255),
                    duration VARCHAR(50),
                    order_index INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_chapter_id (chapter_id),
                    CONSTRAINT fk_lessons_chapter FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课时表'
            ''',
            'learning_progress': '''
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    course_id INT NOT NULL,
                    chapter_id INT,
                    lesson_id INT,
                    progress INT DEFAULT 0,
                    completed TINYINT(1) DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_user_lesson (user_id, lesson_id),
                    KEY idx_user_id (user_id),
                    KEY idx_course_id (course_id),
                    CONSTRAINT fk_progress_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_progress_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                    CONSTRAINT fk_progress_lesson FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习进度表'
            ''',
            'materials': '''
                CREATE TABLE IF NOT EXISTS materials (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    file_url VARCHAR(255) NOT NULL,
                    type VARCHAR(50),
                    uploader_id INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_course_id (course_id),
                    KEY idx_uploader_id (uploader_id),
                    CONSTRAINT fk_materials_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                    CONSTRAINT fk_materials_uploader FOREIGN KEY (uploader_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程资料表'
            ''',
            'discussions': '''
                CREATE TABLE IF NOT EXISTS discussions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    images JSON,
                    category VARCHAR(100) DEFAULT 'general',
                    tags VARCHAR(500),
                    view_count INT DEFAULT 0,
                    like_count INT DEFAULT 0,
                    is_sticky TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_course_id (course_id),
                    KEY idx_user_id (user_id),
                    KEY idx_category (category),
                    KEY idx_created_at (created_at),
                    KEY idx_is_sticky (is_sticky),
                    FULLTEXT KEY ft_title_content (title, content),
                    CONSTRAINT fk_discussions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_discussions_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='讨论区帖子表'
            ''',
            'replies': '''
                CREATE TABLE IF NOT EXISTS replies (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    discussion_id INT NOT NULL,
                    user_id INT NOT NULL,
                    parent_id INT,
                    content TEXT NOT NULL,
                    like_count INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_discussion_id (discussion_id),
                    KEY idx_user_id (user_id),
                    KEY idx_parent_id (parent_id),
                    KEY idx_created_at (created_at),
                    CONSTRAINT fk_replies_discussion FOREIGN KEY (discussion_id) REFERENCES discussions (id) ON DELETE CASCADE,
                    CONSTRAINT fk_replies_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_replies_parent FOREIGN KEY (parent_id) REFERENCES replies (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论回复表'
            ''',
            'discussion_likes': '''
                CREATE TABLE IF NOT EXISTS discussion_likes (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    discussion_id INT NOT NULL,
                    user_id INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_discussion_user (discussion_id, user_id),
                    KEY idx_discussion_id (discussion_id),
                    KEY idx_user_id (user_id),
                    CONSTRAINT fk_dlikes_discussion FOREIGN KEY (discussion_id) REFERENCES discussions (id) ON DELETE CASCADE,
                    CONSTRAINT fk_dlikes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子点赞表'
            ''',
            'reply_likes': '''
                CREATE TABLE IF NOT EXISTS reply_likes (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    reply_id INT NOT NULL,
                    user_id INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_reply_user (reply_id, user_id),
                    KEY idx_reply_id (reply_id),
                    KEY idx_user_id (user_id),
                    CONSTRAINT fk_rlikes_reply FOREIGN KEY (reply_id) REFERENCES replies (id) ON DELETE CASCADE,
                    CONSTRAINT fk_rlikes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论点赞表'
            ''',
            'code_shares': '''
                CREATE TABLE IF NOT EXISTS code_shares (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    code TEXT NOT NULL,
                    description TEXT,
                    language VARCHAR(50) DEFAULT 'cpp',
                    tags VARCHAR(500),
                    view_count INT DEFAULT 0,
                    like_count INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_user_id (user_id),
                    KEY idx_language (language),
                    KEY idx_created_at (created_at),
                    FULLTEXT KEY ft_title_code (title, description),
                    CONSTRAINT fk_codeshares_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码分享表'
            ''',
            'reviews': '''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    course_id INT NOT NULL,
                    user_id INT NOT NULL,
                    rating INT NOT NULL,
                    comment TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_user_course (user_id, course_id),
                    KEY idx_course_id (course_id),
                    KEY idx_rating (rating),
                    CONSTRAINT fk_reviews_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程评价表'
            ''',
            'problem_categories': '''
                CREATE TABLE IF NOT EXISTS problem_categories (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    parent_id INT,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_parent_id (parent_id),
                    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES problem_categories (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目分类表'
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
                    difficulty VARCHAR(50) DEFAULT 'medium',
                    category_id INT,
                    time_limit INT DEFAULT 1,
                    memory_limit INT DEFAULT 256,
                    test_cases JSON,
                    source VARCHAR(100),
                    source_id VARCHAR(100),
                    source_url VARCHAR(500),
                    is_public TINYINT(1) DEFAULT 0,
                    tags VARCHAR(500),
                    hint TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_category_id (category_id),
                    KEY idx_difficulty (difficulty),
                    KEY idx_source (source),
                    KEY idx_is_public (is_public),
                    KEY idx_title (title),
                    FULLTEXT KEY ft_title_description (title, description),
                    CONSTRAINT fk_problems_category FOREIGN KEY (category_id) REFERENCES problem_categories (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='编程题目表'
            ''',
            'submissions': '''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    problem_id INT NOT NULL,
                    code TEXT NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    submit_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_user_id (user_id),
                    KEY idx_problem_id (problem_id),
                    KEY idx_status (status),
                    KEY idx_submit_time (submit_time),
                    CONSTRAINT fk_submissions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_submissions_problem FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码提交记录表'
            ''',
            'ai_conversations': '''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    problem_id INT,
                    question TEXT,
                    answer TEXT,
                    model_name VARCHAR(100),
                    conversation_type VARCHAR(100) DEFAULT 'general',
                    has_code TINYINT(1) DEFAULT 0,
                    has_image TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_user_id (user_id),
                    KEY idx_problem_id (problem_id),
                    KEY idx_model_name (model_name),
                    KEY idx_conversation_type (conversation_type),
                    KEY idx_created_at (created_at),
                    CONSTRAINT fk_aiconv_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_aiconv_problem FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话记录表'
            ''',
            'teacher_assignments': '''
                CREATE TABLE IF NOT EXISTS teacher_assignments (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    teacher_id INT NOT NULL,
                    problem_id INT NOT NULL,
                    title VARCHAR(255),
                    description TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    KEY idx_teacher_id (teacher_id),
                    KEY idx_problem_id (problem_id),
                    KEY idx_end_time (end_time),
                    CONSTRAINT fk_assignments_teacher FOREIGN KEY (teacher_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_assignments_problem FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师作业表'
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_teacher_problem (teacher_id, problem_id),
                    KEY idx_teacher_id (teacher_id),
                    KEY idx_course_id (course_id),
                    CONSTRAINT fk_selected_teacher FOREIGN KEY (teacher_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_selected_problem FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE,
                    CONSTRAINT fk_selected_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师选中题目表'
            ''',
            'problem_import_logs': '''
                CREATE TABLE IF NOT EXISTS problem_import_logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    admin_id INT NOT NULL,
                    source VARCHAR(100),
                    count INT,
                    status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_admin_id (admin_id),
                    KEY idx_status (status),
                    KEY idx_created_at (created_at),
                    CONSTRAINT fk_importlogs_admin FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目导入日志表'
            ''',
            'caigpt_dialog_history': '''
                CREATE TABLE IF NOT EXISTS caigpt_dialog_history (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    images JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_user_id (user_id),
                    KEY idx_role (role),
                    KEY idx_created_at (created_at),
                    CONSTRAINT fk_caigpt_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CaiGPT对话历史表'
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

        try:
            cursor.execute("SHOW COLUMNS FROM users LIKE 'bio'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT AFTER avatar")
                conn.commit()
                print('[OK] Added missing bio column to users table')
        except Exception as e:
            print(f'[WARN] Could not check/add bio column: {e}')

        try:
            cursor.execute("SHOW COLUMNS FROM discussions LIKE 'lesson_id'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE discussions ADD COLUMN lesson_id INT AFTER course_id")
                cursor.execute("ALTER TABLE discussions ADD INDEX idx_lesson_id (lesson_id)")
                conn.commit()
                print('[OK] Added missing lesson_id column to discussions table')
        except Exception as e:
            print(f'[WARN] Could not check/add lesson_id column: {e}')

        try:
            cursor.execute("SHOW COLUMNS FROM lessons LIKE 'media_files'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lessons ADD COLUMN media_files TEXT AFTER content")
                conn.commit()
                print('[OK] Added missing media_files column to lessons table')
        except Exception as e:
            print(f'[WARN] Could not check/add media_files column: {e}')

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
        max_retries = 3
        for attempt in range(max_retries):
            conn = self.get_connection()
            if not conn:
                if attempt < max_retries - 1:
                    print(f'[WARN] Retry {attempt + 1}/{max_retries}: Getting new connection...')
                    self.conn = None
                    time.sleep(0.5)
                    continue
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
            except mysql.connector.Error as e:
                print(f'[WARN] MySQL Error (attempt {attempt + 1}/{max_retries}): {e}')
                if attempt < max_retries - 1:
                    self.conn = None
                    try:
                        if conn.is_connected():
                            conn.close()
                    except:
                        pass
                    time.sleep(0.5 * (attempt + 1))
                    continue
                print(f'[ERR] Error updating {table_name} record after {max_retries} attempts: {e}')
                return False
            except Exception as e:
                print(f'[ERR] Error updating {table_name} record: {e}')
                return False
        
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
