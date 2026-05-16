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

        self._ssl_disabled = not os.environ.get('MYSQL_SSL', '').lower() in ('true', '1', 'yes')
        self._pool_size = int(os.environ.get('MYSQL_POOL_SIZE', '5'))
        self._auth_plugin = os.environ.get('MYSQL_AUTH_PLUGIN', 'mysql_native_password')

        self._ensure_database_exists()
        self._create_pool_with_retry()
        
        try:
            self.get_connection()
            if self.conn:
                self.create_tables()
        except Exception as e:
            print(f'[ERR] Database initialization failed: {e}')
    
    def _ensure_database_exists(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                autocommit=True,
                ssl_disabled=self._ssl_disabled,
                auth_plugin=self._auth_plugin
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            conn.close()
            print(f'[OK] Database `{self.database}` ensured')
        except Exception as e:
            print(f'[WARN] Could not ensure database exists: {e}')

    def _create_pool_with_retry(self, max_retries=3, retry_delay=2):
        for attempt in range(max_retries):
            try:
                self._connection_pool = pooling.MySQLConnectionPool(
                    pool_name=f'learning_platform_pool_{id(self)}',
                    pool_size=self._pool_size,
                    pool_reset_session=True,
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    port=self.port,
                    autocommit=True,
                    ssl_disabled=self._ssl_disabled,
                    auth_plugin=self._auth_plugin
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
                autocommit=True,
                ssl_disabled=self._ssl_disabled,
                auth_plugin=self._auth_plugin
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
                    media_files LONGTEXT,
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
                    ai_analysis TEXT,
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
                    session_id INT,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    images JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_role (role),
                    INDEX idx_created_at (created_at),
                    INDEX idx_user_session (user_id, session_id),
                    CONSTRAINT fk_caigpt_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CaiGPT对话历史表'
            ''',
            'caigpt_sessions': '''
                CREATE TABLE IF NOT EXISTS caigpt_sessions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    title VARCHAR(200) DEFAULT '新对话',
                    model_name VARCHAR(50) DEFAULT 'caigpt',
                    problem_id INT,
                    tags JSON,
                    is_favorite TINYINT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CAIgpt会话表'
            ''',
            'caigpt_favorites': '''
                CREATE TABLE IF NOT EXISTS caigpt_favorites (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    session_id INT NOT NULL,
                    message_id INT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_favorite (user_id, session_id, message_id),
                    INDEX idx_user_id (user_id),
                    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    CONSTRAINT fk_favorites_session FOREIGN KEY (session_id) REFERENCES caigpt_sessions (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CAIgpt收藏表'
            ''',
            'ai_user_preferences': '''
                CREATE TABLE IF NOT EXISTS ai_user_preferences (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL UNIQUE,
                    theme VARCHAR(20) DEFAULT 'light',
                    editor_theme VARCHAR(30) DEFAULT 'vs-dark',
                    editor_font_size INT DEFAULT 14,
                    editor_font_family VARCHAR(100) DEFAULT "'Consolas', 'Monaco', 'Courier New', monospace",
                    editor_word_wrap VARCHAR(10) DEFAULT 'on',
                    minimap_enabled TINYINT DEFAULT 1,
                    auto_save_enabled TINYINT DEFAULT 1,
                    last_code LONGTEXT,
                    last_session_id INT,
                    language VARCHAR(10) DEFAULT 'cpp',
                    model_preference VARCHAR(50) DEFAULT 'caigpt',
                    ui_layout VARCHAR(20) DEFAULT 'split',
                    console_height INT DEFAULT 200,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    CONSTRAINT fk_preferences_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI用户偏好设置表'
            ''',
            'ai_memory': '''
                CREATE TABLE IF NOT EXISTS ai_memory (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    memory_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    source_session_id INT DEFAULT NULL,
                    importance TINYINT DEFAULT 5,
                    access_count INT DEFAULT 0,
                    tags JSON DEFAULT NULL,
                    is_active TINYINT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_type (user_id, memory_type),
                    INDEX idx_user_active (user_id, is_active),
                    INDEX idx_user_importance (user_id, importance),
                    INDEX idx_created_at (created_at),
                    FULLTEXT INDEX ft_content (content),
                    CONSTRAINT fk_memory_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI助手记忆表'
            ''',
            'ai_memory_summary': '''
                CREATE TABLE IF NOT EXISTS ai_memory_summary (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL UNIQUE,
                    summary TEXT,
                    last_memory_count INT DEFAULT 0,
                    last_summary_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    CONSTRAINT fk_memory_summary_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI记忆摘要表'
            ''',
            'knowledge_topics': '''
                CREATE TABLE IF NOT EXISTS knowledge_topics (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    category VARCHAR(100) NOT NULL COMMENT '知识分类',
                    keyword VARCHAR(100) NOT NULL COMMENT '关键词',
                    description TEXT COMMENT '分类描述',
                    estimated_time VARCHAR(50) COMMENT '预计学习时间',
                    sort_order INT DEFAULT 0 COMMENT '排序',
                    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识点分类表'
            ''',
            'learning_resources': '''
                CREATE TABLE IF NOT EXISTS learning_resources (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    category VARCHAR(100) NOT NULL COMMENT '所属知识分类',
                    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型: course/practice/project',
                    title VARCHAR(200) NOT NULL COMMENT '资源标题',
                    description TEXT COMMENT '资源描述',
                    url VARCHAR(500) DEFAULT NULL COMMENT '资源链接',
                    sort_order INT DEFAULT 0 COMMENT '排序',
                    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_type (resource_type),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习资源表'
            ''',
            'common_errors': '''
                CREATE TABLE IF NOT EXISTS common_errors (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    error_type VARCHAR(100) NOT NULL COMMENT '错误类型标识',
                    pattern VARCHAR(500) NOT NULL COMMENT '匹配正则表达式',
                    cause TEXT NOT NULL COMMENT '错误原因',
                    solutions JSON NOT NULL COMMENT '解决方案列表',
                    sort_order INT DEFAULT 0 COMMENT '排序',
                    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_error_type (error_type),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='常见错误表'
            ''',
            'ai_models': '''
                CREATE TABLE IF NOT EXISTS ai_models (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    model_key VARCHAR(50) NOT NULL UNIQUE COMMENT '模型标识',
                    name VARCHAR(200) NOT NULL COMMENT '模型显示名称',
                    api_url VARCHAR(500) DEFAULT 'local' COMMENT 'API地址',
                    api_key VARCHAR(500) DEFAULT '' COMMENT 'API密钥',
                    model VARCHAR(100) DEFAULT '' COMMENT '模型名称',
                    provider VARCHAR(50) DEFAULT '' COMMENT '提供者',
                    is_cloud TINYINT DEFAULT 0 COMMENT '是否云端: 0/1',
                    max_tokens INT DEFAULT 4096 COMMENT '最大token数',
                    temperature DECIMAL(3,2) DEFAULT 0.70 COMMENT '温度参数',
                    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
                    sort_order INT DEFAULT 0 COMMENT '排序',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_model_key (model_key),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI模型配置表'
            ''',
            'site_settings': '''
                CREATE TABLE IF NOT EXISTS site_settings (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    setting_key VARCHAR(100) NOT NULL UNIQUE,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_setting_key (setting_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='站点设置表'
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
                cursor.execute("ALTER TABLE lessons ADD COLUMN media_files LONGTEXT AFTER content")
                conn.commit()
                print('[OK] Added missing media_files column to lessons table (LONGTEXT)')
            else:
                # 检查字段类型，如果是 TEXT 则升级为 LONGTEXT
                cursor.execute("""
                    SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'lessons' AND COLUMN_NAME = 'media_files'
                """)
                result = cursor.fetchone()
                if result and 'text' in result[0].lower() and 'long' not in result[0].lower():
                    print(f'[INFO] Upgrading media_files column from {result[0]} to LONGTEXT...')
                    cursor.execute("ALTER TABLE lessons MODIFY COLUMN media_files LONGTEXT")
                    conn.commit()
                    print('[OK] ✅ Successfully upgraded media_files column to LONGTEXT (supports up to 4GB)')
        except Exception as e:
            print(f'[WARN] Could not check/add/upgrade media_files column: {e}')

        self._init_default_data(cursor, conn)

        cursor.close()
    
    def _init_default_data(self, cursor, conn):
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_topics")
            result = cursor.fetchone()
            count = result[0] if isinstance(result, tuple) else result.get('cnt', 0)
            if count == 0:
                default_topics = [
                    ('基础语法', 'Hello World', '掌握C++的基本语法，包括变量、数据类型、运算符等', '2-3天', 1),
                    ('基础语法', '变量', '掌握C++的基本语法，包括变量、数据类型、运算符等', '2-3天', 2),
                    ('基础语法', '数据类型', '掌握C++的基本语法，包括变量、数据类型、运算符等', '2-3天', 3),
                    ('基础语法', '运算符', '掌握C++的基本语法，包括变量、数据类型、运算符等', '2-3天', 4),
                    ('基础语法', '输入输出', '掌握C++的基本语法，包括变量、数据类型、运算符等', '2-3天', 5),
                    ('控制结构', '循环', '学习条件语句和循环语句，控制程序执行流程', '3-5天', 1),
                    ('控制结构', '条件语句', '学习条件语句和循环语句，控制程序执行流程', '3-5天', 2),
                    ('控制结构', 'switch', '学习条件语句和循环语句，控制程序执行流程', '3-5天', 3),
                    ('控制结构', 'break', '学习条件语句和循环语句，控制程序执行流程', '3-5天', 4),
                    ('控制结构', 'continue', '学习条件语句和循环语句，控制程序执行流程', '3-5天', 5),
                    ('函数', '函数定义', '理解函数的定义、调用、参数传递和递归', '5-7天', 1),
                    ('函数', '参数传递', '理解函数的定义、调用、参数传递和递归', '5-7天', 2),
                    ('函数', '递归', '理解函数的定义、调用、参数传递和递归', '5-7天', 3),
                    ('函数', '函数重载', '理解函数的定义、调用、参数传递和递归', '5-7天', 4),
                    ('数组和指针', '数组', '深入理解数组和指针，掌握内存管理', '7-10天', 1),
                    ('数组和指针', '指针', '深入理解数组和指针，掌握内存管理', '7-10天', 2),
                    ('数组和指针', '引用', '深入理解数组和指针，掌握内存管理', '7-10天', 3),
                    ('数组和指针', '动态内存', '深入理解数组和指针，掌握内存管理', '7-10天', 4),
                    ('面向对象', '类', '学习类、对象、继承、多态等OOP概念', '10-14天', 1),
                    ('面向对象', '继承', '学习类、对象、继承、多态等OOP概念', '10-14天', 2),
                    ('面向对象', '多态', '学习类、对象、继承、多态等OOP概念', '10-14天', 3),
                    ('面向对象', '封装', '学习类、对象、继承、多态等OOP概念', '10-14天', 4),
                    ('面向对象', '构造函数', '学习类、对象、继承、多态等OOP概念', '10-14天', 5),
                    ('面向对象', '析构函数', '学习类、对象、继承、多态等OOP概念', '10-14天', 6),
                    ('STL', 'vector', '掌握C++标准模板库的使用', '7-10天', 1),
                    ('STL', 'map', '掌握C++标准模板库的使用', '7-10天', 2),
                    ('STL', 'set', '掌握C++标准模板库的使用', '7-10天', 3),
                    ('STL', 'stack', '掌握C++标准模板库的使用', '7-10天', 4),
                    ('STL', 'queue', '掌握C++标准模板库的使用', '7-10天', 5),
                    ('STL', '迭代器', '掌握C++标准模板库的使用', '7-10天', 6),
                    ('高级特性', '模板', '学习模板、异常处理、文件操作等高级特性', '10-14天', 1),
                    ('高级特性', '异常处理', '学习模板、异常处理、文件操作等高级特性', '10-14天', 2),
                    ('高级特性', '文件操作', '学习模板、异常处理、文件操作等高级特性', '10-14天', 3),
                    ('高级特性', '命名空间', '学习模板、异常处理、文件操作等高级特性', '10-14天', 4),
                    ('高级特性', 'lambda', '学习模板、异常处理、文件操作等高级特性', '10-14天', 5),
                    ('数据结构', '链表', '掌握常用数据结构的实现和应用', '14-21天', 1),
                    ('数据结构', '栈和队列', '掌握常用数据结构的实现和应用', '14-21天', 2),
                    ('数据结构', '二叉树', '掌握常用数据结构的实现和应用', '14-21天', 3),
                    ('数据结构', '哈希表', '掌握常用数据结构的实现和应用', '14-21天', 4),
                    ('数据结构', '图', '掌握常用数据结构的实现和应用', '14-21天', 5),
                    ('算法', '排序', '学习常用算法，提高编程能力', '21-30天', 1),
                    ('算法', '查找', '学习常用算法，提高编程能力', '21-30天', 2),
                    ('算法', '递归', '学习常用算法，提高编程能力', '21-30天', 3),
                    ('算法', '动态规划', '学习常用算法，提高编程能力', '21-30天', 4),
                    ('算法', '贪心算法', '学习常用算法，提高编程能力', '21-30天', 5),
                ]
                cursor.executemany(
                    'INSERT INTO knowledge_topics (category, keyword, description, estimated_time, sort_order) VALUES (%s, %s, %s, %s, %s)',
                    default_topics
                )
                conn.commit()
                print(f'[OK] Inserted {len(default_topics)} default knowledge topics')
        except Exception as e:
            print(f'[WARN] Could not init knowledge_topics: {e}')

        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM learning_resources")
            result = cursor.fetchone()
            count = result[0] if isinstance(result, tuple) else result.get('cnt', 0)
            if count == 0:
                default_resources = [
                    ('基础语法', 'course', 'C++基础入门', '学习C++基本语法和概念', 1),
                    ('基础语法', 'practice', '基础练习题', '变量、数据类型和运算符练习', 2),
                    ('控制结构', 'course', '流程控制', '掌握if、for、while等控制语句', 1),
                    ('控制结构', 'practice', '循环练习', '各种循环结构的练习题', 2),
                    ('函数', 'course', '函数与递归', '函数定义、调用和递归思想', 1),
                    ('函数', 'practice', '函数练习题', '函数定义和递归算法练习', 2),
                    ('数组和指针', 'course', '指针与内存', '深入理解指针和内存管理', 1),
                    ('数组和指针', 'practice', '指针练习', '指针操作和动态内存分配', 2),
                    ('面向对象', 'course', '面向对象编程', '类、对象、继承和多态', 1),
                    ('面向对象', 'practice', 'OOP练习', '类和对象的实践练习', 2),
                    ('STL', 'course', 'STL标准库', '掌握vector、map等容器', 1),
                    ('STL', 'practice', 'STL练习', 'STL容器的使用练习', 2),
                    ('高级特性', 'course', 'C++高级特性', '模板、异常、文件操作', 1),
                    ('高级特性', 'practice', '高级练习', '模板和异常处理练习', 2),
                    ('数据结构', 'course', '数据结构基础', '链表、栈、队列、树', 1),
                    ('数据结构', 'practice', '数据结构练习', '实现各种数据结构', 2),
                    ('算法', 'course', '算法基础', '排序、查找、递归、DP', 1),
                    ('算法', 'practice', '算法练习', '经典算法题目练习', 2),
                ]
                cursor.executemany(
                    'INSERT INTO learning_resources (category, resource_type, title, description, sort_order) VALUES (%s, %s, %s, %s, %s)',
                    default_resources
                )
                conn.commit()
                print(f'[OK] Inserted {len(default_resources)} default learning resources')
        except Exception as e:
            print(f'[WARN] Could not init learning_resources: {e}')

        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM common_errors")
            result = cursor.fetchone()
            count = result[0] if isinstance(result, tuple) else result.get('cnt', 0)
            if count == 0:
                import json as _json
                default_errors = [
                    ('segmentation fault', r'Segmentation fault|段错误', '访问了非法内存地址',
                     _json.dumps(['检查指针是否初始化', '确保不要访问已释放的内存', '检查数组下标是否越界', '使用调试器定位问题']), 1),
                    ('memory leak', r'memory leak|内存泄漏', '动态分配的内存未释放',
                     _json.dumps(['使用智能指针管理内存', '确保每个new都有对应的delete', '使用RAII模式', '使用valgrind检测内存泄漏']), 2),
                    ('undefined reference', r'undefined reference|未定义引用', '函数声明但未定义，或缺少库文件',
                     _json.dumps(['检查函数是否有定义', '确保所有源文件都被编译', '检查链接的库文件', '检查函数签名是否匹配']), 3),
                    ('array bounds', r'array subscript|数组越界', '访问了数组范围之外的元素',
                     _json.dumps(['检查数组下标范围', '使用STL容器的at()方法', '添加边界检查', '考虑使用动态数组']), 4),
                ]
                cursor.executemany(
                    'INSERT INTO common_errors (error_type, pattern, cause, solutions, sort_order) VALUES (%s, %s, %s, %s, %s)',
                    default_errors
                )
                conn.commit()
                print(f'[OK] Inserted {len(default_errors)} default common errors')
        except Exception as e:
            print(f'[WARN] Could not init common_errors: {e}')

        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM ai_models")
            result = cursor.fetchone()
            count = result[0] if isinstance(result, tuple) else result.get('cnt', 0)
            if count == 0:
                import os as _os
                default_models = [
                    ('auto', 'CAIgpt', 'local', '', 'caigpt', 'caigpt', 0, 4096, 0.70, 1, 1),
                    ('caigpt', 'CAIgpt', 'local', '', 'caigpt', 'caigpt', 0, 4096, 0.70, 1, 2),
                    ('minimax', 'Minimax M2.7', 'cloud', _os.environ.get('MINIMAX_API_KEY', ''), 'Minimax-Text-01', 'minimax', 1, 4096, 0.70, 1, 3),
                    ('ollama', 'CAIgpt 本地版 (Ollama)', 'local', '', 'qwen3:8b', 'ollama', 0, 4096, 0.70, 1, 4),
                    ('qwen', '通义千问', 'cloud', _os.environ.get('DASHSCOPE_API_KEY', ''), 'qwen-plus', 'qwen', 1, 4096, 0.70, 1, 5),
                    ('local', '本地模拟', 'local', '', 'local', 'local', 0, 4096, 0.70, 0, 6),
                ]
                cursor.executemany(
                    'INSERT INTO ai_models (model_key, name, api_url, api_key, model, provider, is_cloud, max_tokens, temperature, is_active, sort_order) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    default_models
                )
                conn.commit()
                print(f'[OK] Inserted {len(default_models)} default AI models')
        except Exception as e:
            print(f'[WARN] Could not init ai_models: {e}')

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
                    except Exception:
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
                cursor.close()
                return self._convert_datetime_to_string(row)
            else:
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
