-- =====================================================
-- C语言学习平台 - MySQL数据库完整初始化脚本
-- 数据库: learning_platform
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
-- 创建时间: 2026-04-02
-- =====================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. 用户表 (users)
-- 存储所有用户信息：管理员、教师、学生
-- =====================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(255) NOT NULL COMMENT '用户名',
    `email` VARCHAR(255) NOT NULL COMMENT '邮箱',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    `role` VARCHAR(50) NOT NULL DEFAULT 'student' COMMENT '角色: admin/teacher/student',
    `nickname` VARCHAR(255) DEFAULT NULL COMMENT '昵称',
    `avatar` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    KEY `idx_role` (`role`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- =====================================================
-- 2. 课程表 (courses)
-- 存储课程基本信息
-- =====================================================
DROP TABLE IF EXISTS `courses`;
CREATE TABLE `courses` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '课程ID',
    `title` VARCHAR(255) NOT NULL COMMENT '课程标题',
    `description` TEXT COMMENT '课程描述',
    `teacher_id` INT DEFAULT NULL COMMENT '授课教师ID',
    `category` VARCHAR(100) DEFAULT NULL COMMENT '课程分类',
    `cover` VARCHAR(255) DEFAULT NULL COMMENT '封面图片URL',
    `status` VARCHAR(50) DEFAULT 'draft' COMMENT '状态: draft/published/archived',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_teacher_id` (`teacher_id`),
    KEY `idx_category` (`category`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_courses_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程表';

-- =====================================================
-- 3. 章节表 (chapters)
-- 课程下的章节划分
-- =====================================================
DROP TABLE IF EXISTS `chapters`;
CREATE TABLE `chapters` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '章节ID',
    `course_id` INT NOT NULL COMMENT '所属课程ID',
    `title` VARCHAR(255) NOT NULL COMMENT '章节标题',
    `order_index` INT DEFAULT 0 COMMENT '排序序号',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_course_id` (`course_id`),
    CONSTRAINT `fk_chapters_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='章节表';

-- =====================================================
-- 4. 课时/课程内容表 (lessons)
-- 章节下的具体课时，包含视频、文档等内容
-- =====================================================
DROP TABLE IF EXISTS `lessons`;
CREATE TABLE `lessons` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '课时ID',
    `chapter_id` INT NOT NULL COMMENT '所属章节ID',
    `title` VARCHAR(255) NOT NULL COMMENT '课时标题',
    `description` TEXT COMMENT '课时描述',
    `content` TEXT COMMENT '课时内容（富文本/Markdown）',
    `content_type` VARCHAR(50) DEFAULT 'text' COMMENT '内容类型: text/video/document',
    `content_path` VARCHAR(255) DEFAULT NULL COMMENT '内容文件路径（视频/文档）',
    `duration` VARCHAR(50) DEFAULT NULL COMMENT '时长（视频用）',
    `order_index` INT DEFAULT 0 COMMENT '排序序号',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_chapter_id` (`chapter_id`),
    CONSTRAINT `fk_lessons_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课时表';

-- =====================================================
-- 5. 学习进度表 (learning_progress)
-- 记录学生的学习进度
-- =====================================================
DROP TABLE IF EXISTS `learning_progress`;
CREATE TABLE `learning_progress` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '进度记录ID',
    `user_id` INT NOT NULL COMMENT '学生用户ID',
    `course_id` INT NOT NULL COMMENT '课程ID',
    `chapter_id` INT DEFAULT NULL COMMENT '章节ID',
    `lesson_id` INT DEFAULT NULL COMMENT '课时ID',
    `progress` INT DEFAULT 0 COMMENT '学习进度百分比 (0-100)',
    `completed` TINYINT(1) DEFAULT 0 COMMENT '是否完成: 0/1',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_lesson` (`user_id`, `lesson_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_course_id` (`course_id`),
    CONSTRAINT `fk_progress_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_progress_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_progress_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习进度表';

-- =====================================================
-- 6. 课程资料表 (materials)
-- 教师上传的课程相关资料文件
-- =====================================================
DROP TABLE IF EXISTS `materials`;
CREATE TABLE `materials` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '资料ID',
    `course_id` INT NOT NULL COMMENT '所属课程ID',
    `title` VARCHAR(255) NOT NULL COMMENT '资料标题',
    `file_url` VARCHAR(255) NOT NULL COMMENT '文件存储路径',
    `type` VARCHAR(50) DEFAULT NULL COMMENT '文件类型: pdf/doc/xls等',
    `uploader_id` INT NOT NULL COMMENT '上传者ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_course_id` (`course_id`),
    KEY `idx_uploader_id` (`uploader_id`),
    CONSTRAINT `fk_materials_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_materials_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程资料表';

-- =====================================================
-- 7. 课程评价表 (reviews)
-- 学生对课程的评价和评分
-- =====================================================
DROP TABLE IF EXISTS `reviews`;
CREATE TABLE `reviews` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '评价ID',
    `course_id` INT NOT NULL COMMENT '课程ID',
    `user_id` INT NOT NULL COMMENT '评价用户ID',
    `rating` INT NOT NULL COMMENT '评分 (1-5星)',
    `comment` TEXT COMMENT '评价内容',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_course` (`user_id`, `course_id`),
    KEY `idx_course_id` (`course_id`),
    KEY `idx_rating` (`rating`),
    CONSTRAINT `fk_reviews_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_reviews_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程评价表';

-- =====================================================
-- 8. 题目分类表 (problem_categories)
-- 编程题目的分类体系（支持多级分类）
-- =====================================================
DROP TABLE IF EXISTS `problem_categories`;
CREATE TABLE `problem_categories` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '分类ID',
    `name` VARCHAR(255) NOT NULL COMMENT '分类名称',
    `parent_id` INT DEFAULT NULL COMMENT '父分类ID（NULL表示顶级分类）',
    `description` TEXT COMMENT '分类描述',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_parent_id` (`parent_id`),
    CONSTRAINT `fk_categories_parent` FOREIGN KEY (`parent_id`) REFERENCES `problem_categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目分类表';

-- =====================================================
-- 9. 编程题目表 (problems)
-- 核心题库，存储C/C++编程题目
-- =====================================================
DROP TABLE IF EXISTS `problems`;
CREATE TABLE `problems` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '题目ID',
    `title` VARCHAR(255) NOT NULL COMMENT '题目标题',
    `description` TEXT COMMENT '题目描述',
    `input_format` TEXT COMMENT '输入格式说明',
    `output_format` TEXT COMMENT '输出格式说明',
    `sample_input` TEXT COMMENT '样例输入',
    `sample_output` TEXT COMMENT '样例输出',
    `difficulty` VARCHAR(50) DEFAULT 'medium' COMMENT '难度: easy/medium/hard',
    `category_id` INT DEFAULT NULL COMMENT '所属分类ID',
    `time_limit` INT DEFAULT 1 COMMENT '时间限制（秒）',
    `memory_limit` INT DEFAULT 256 COMMENT '内存限制（MB）',
    `test_cases` JSON COMMENT '测试用例（JSON数组）',
    `source` VARCHAR(100) DEFAULT NULL COMMENT '来源平台: luogu/hdoj/leetcode等',
    `source_id` VARCHAR(100) DEFAULT NULL COMMENT '来源平台题目ID',
    `source_url` VARCHAR(500) DEFAULT NULL COMMENT '来源链接',
    `is_public` TINYINT(1) DEFAULT 0 COMMENT '是否公开: 0/1',
    `tags` VARCHAR(500) DEFAULT NULL COMMENT '标签（JSON数组字符串）',
    `hint` TEXT COMMENT '提示信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_difficulty` (`difficulty`),
    KEY `idx_source` (`source`),
    KEY `idx_is_public` (`is_public`),
    KEY `idx_title` (`title`),
    FULLTEXT KEY `ft_title_description` (`title`, `description`),
    CONSTRAINT `fk_problems_category` FOREIGN KEY (`category_id`) REFERENCES `problem_categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='编程题目表';

-- =====================================================
-- 10. 代码提交记录表 (submissions)
-- 学生提交代码的评测记录
-- =====================================================
DROP TABLE IF EXISTS `submissions`;
CREATE TABLE `submissions` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '提交记录ID',
    `user_id` INT NOT NULL COMMENT '提交用户ID',
    `problem_id` INT NOT NULL COMMENT '题目ID',
    `code` TEXT NOT NULL COMMENT '提交的代码',
    `status` VARCHAR(50) DEFAULT 'pending' COMMENT '评测状态: AC/WA/TLE/MLE/CE/RE/pending',
    `error_message` TEXT COMMENT '错误信息',
    `submit_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_problem_id` (`problem_id`),
    KEY `idx_status` (`status`),
    KEY `idx_submit_time` (`submit_time`),
    CONSTRAINT `fk_submissions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_submissions_problem` FOREIGN KEY (`problem_id`) REFERENCES `problems` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码提交记录表';

-- =====================================================
-- 11. 教师作业表 (teacher_assignments)
-- 教师布置的作业任务
-- =====================================================
DROP TABLE IF EXISTS `teacher_assignments`;
CREATE TABLE `teacher_assignments` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '作业ID',
    `teacher_id` INT NOT NULL COMMENT '教师用户ID',
    `problem_id` INT NOT NULL COMMENT '关联题目ID',
    `title` VARCHAR(255) DEFAULT NULL COMMENT '作业标题',
    `description` TEXT COMMENT '作业描述',
    `start_time` DATETIME DEFAULT NULL COMMENT '开始时间',
    `end_time` DATETIME DEFAULT NULL COMMENT '截止时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_teacher_id` (`teacher_id`),
    KEY `idx_problem_id` (`problem_id`),
    KEY `idx_end_time` (`end_time`),
    CONSTRAINT `fk_assignments_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_assignments_problem` FOREIGN KEY (`problem_id`) REFERENCES `problems` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师作业表';

-- =====================================================
-- 12. 教师选中题目表 (teacher_selected_problems)
-- 教师为课程选择的练习题目
-- =====================================================
DROP TABLE IF EXISTS `teacher_selected_problems`;
CREATE TABLE `teacher_selected_problems` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `teacher_id` INT NOT NULL COMMENT '教师用户ID',
    `problem_id` INT NOT NULL COMMENT '题目ID',
    `course_id` INT DEFAULT NULL COMMENT '关联课程ID',
    `selected_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '选择时间',
    `visible_start` DATETIME DEFAULT NULL COMMENT '可见开始时间',
    `visible_end` DATETIME DEFAULT NULL COMMENT '可见结束时间',
    `notes` TEXT COMMENT '备注说明',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_teacher_problem` (`teacher_id`, `problem_id`),
    KEY `idx_teacher_id` (`teacher_id`),
    KEY `idx_course_id` (`course_id`),
    CONSTRAINT `fk_selected_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_selected_problem` FOREIGN KEY (`problem_id`) REFERENCES `problems` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_selected_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师选中题目表';

-- =====================================================
-- 13. 讨论区帖子表 (discussions)
-- 社区讨论帖子（贴吧风格）
-- =====================================================
DROP TABLE IF EXISTS `discussions`;
CREATE TABLE `discussions` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
    `course_id` INT DEFAULT NULL COMMENT '关联课程ID（可选）',
    `user_id` INT NOT NULL COMMENT '发帖用户ID',
    `title` VARCHAR(255) NOT NULL COMMENT '帖子标题',
    `content` TEXT COMMENT '帖子内容',
    `images` JSON COMMENT '图片列表（JSON数组）',
    `category` VARCHAR(100) DEFAULT 'general' COMMENT '分类: general/announcement/question/share',
    `tags` VARCHAR(500) DEFAULT NULL COMMENT '标签（逗号分隔）',
    `view_count` INT DEFAULT 0 COMMENT '浏览次数',
    `like_count` INT DEFAULT 0 COMMENT '点赞数',
    `is_sticky` TINYINT(1) DEFAULT 0 COMMENT '是否置顶: 0/1',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_course_id` (`course_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_category` (`category`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_is_sticky` (`is_sticky`),
    FULLTEXT KEY `ft_title_content` (`title`, `content`),
    CONSTRAINT `fk_discussions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_discussions_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='讨论区帖子表';

-- =====================================================
-- 14. 评论/回复表 (replies)
-- 帖子的评论和嵌套回复（抖音风格）
-- =====================================================
DROP TABLE IF EXISTS `replies`;
CREATE TABLE `replies` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '评论ID',
    `discussion_id` INT NOT NULL COMMENT '所属帖子ID',
    `user_id` INT NOT NULL COMMENT '评论用户ID',
    `parent_id` INT DEFAULT NULL COMMENT '父评论ID（NULL表示根评论）',
    `content` TEXT NOT NULL COMMENT '评论内容',
    `like_count` INT DEFAULT 0 COMMENT '点赞数',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_discussion_id` (`discussion_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_parent_id` (`parent_id`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_replies_discussion` FOREIGN KEY (`discussion_id`) REFERENCES `discussions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_replies_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_replies_parent` FOREIGN KEY (`parent_id`) REFERENCES `replies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论回复表';

-- =====================================================
-- 15. 帖子点赞表 (discussion_likes)
-- 记录用户对帖子的点赞
-- =====================================================
DROP TABLE IF EXISTS `discussion_likes`;
CREATE TABLE `discussion_likes` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '点赞记录ID',
    `discussion_id` INT NOT NULL COMMENT '帖子ID',
    `user_id` INT NOT NULL COMMENT '点赞用户ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_discussion_user` (`discussion_id`, `user_id`),
    KEY `idx_discussion_id` (`discussion_id`),
    KEY `idx_user_id` (`user_id`),
    CONSTRAINT `fk_dlikes_discussion` FOREIGN KEY (`discussion_id`) REFERENCES `discussions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_dlikes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子点赞表';

-- =====================================================
-- 16. 评论点赞表 (reply_likes)
-- 记录用户对评论的点赞
-- =====================================================
DROP TABLE IF EXISTS `reply_likes`;
CREATE TABLE `reply_likes` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '点赞记录ID',
    `reply_id` INT NOT NULL COMMENT '评论ID',
    `user_id` INT NOT NULL COMMENT '点赞用户ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_reply_user` (`reply_id`, `user_id`),
    KEY `idx_reply_id` (`reply_id`),
    KEY `idx_user_id` (`user_id`),
    CONSTRAINT `fk_rlikes_reply` FOREIGN KEY (`reply_id`) REFERENCES `replies` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rlikes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论点赞表';

-- =====================================================
-- 17. 代码分享表 (code_shares)
-- 社区代码分享功能
-- =====================================================
DROP TABLE IF EXISTS `code_shares`;
CREATE TABLE `code_shares` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '分享ID',
    `user_id` INT NOT NULL COMMENT '分享用户ID',
    `title` VARCHAR(255) NOT NULL COMMENT '分享标题',
    `code` TEXT NOT NULL COMMENT '代码内容',
    `description` TEXT COMMENT '描述说明',
    `language` VARCHAR(50) DEFAULT 'cpp' COMMENT '编程语言',
    `tags` VARCHAR(500) DEFAULT NULL COMMENT '标签（逗号分隔）',
    `view_count` INT DEFAULT 0 COMMENT '浏览次数',
    `like_count` INT DEFAULT 0 COMMENT '点赞数',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_language` (`language`),
    KEY `idx_created_at` (`created_at`),
    FULLTEXT KEY `ft_title_code` (`title`, `description`),
    CONSTRAINT `fk_codeshares_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码分享表';

-- =====================================================
-- 18. AI对话记录表 (ai_conversations)
-- AI助手与用户的对话历史
-- =====================================================
DROP TABLE IF EXISTS `ai_conversations`;
CREATE TABLE `ai_conversations` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '对话ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `problem_id` INT DEFAULT NULL COMMENT '关联题目ID（可选）',
    `question` TEXT COMMENT '用户问题',
    `answer` TEXT COMMENT 'AI回答',
    `model_name` VARCHAR(100) DEFAULT NULL COMMENT '使用的AI模型名称',
    `conversation_type` VARCHAR(100) DEFAULT 'general' COMMENT '对话类型: general/code_help/explanation',
    `has_code` TINYINT(1) DEFAULT 0 COMMENT '是否包含代码: 0/1',
    `has_image` TINYINT(1) DEFAULT 0 COMMENT '是否包含图片: 0/1',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_problem_id` (`problem_id`),
    KEY `idx_model_name` (`model_name`),
    KEY `idx_conversation_type` (`conversation_type`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_aiconv_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_aiconv_problem` FOREIGN KEY (`problem_id`) REFERENCES `problems` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话记录表';

-- =====================================================
-- 19. CaiGPT对话历史表 (caigpt_dialog_history)
-- CaiGPT专用对话历史（支持图片）
-- =====================================================
DROP TABLE IF EXISTS `caigpt_dialog_history`;
CREATE TABLE `caigpt_dialog_history` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `role` VARCHAR(50) NOT NULL COMMENT '角色: user/assistant/system',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `images` JSON DEFAULT NULL COMMENT '图片列表（JSON数组）',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_role` (`role`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_caigpt_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CaiGPT对话历史表';

-- =====================================================
-- 20. 题目导入日志表 (problem_import_logs)
-- 记录管理员批量导入题目的操作日志
-- =====================================================
DROP TABLE IF EXISTS `problem_import_logs`;
CREATE TABLE `problem_import_logs` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `admin_id` INT NOT NULL COMMENT '操作管理员ID',
    `source` VARCHAR(100) DEFAULT NULL COMMENT '数据来源',
    `count` INT DEFAULT NULL COMMENT '导入数量',
    `status` VARCHAR(50) DEFAULT 'pending' COMMENT '状态: success/failed/pending',
    `error_message` TEXT COMMENT '错误信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_admin_id` (`admin_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_importlogs_admin` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目导入日志表';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 初始化基础数据
-- =====================================================

-- 插入默认题目分类
INSERT INTO `problem_categories` (`name`, `parent_id`, `description`) VALUES
('入门基础', NULL, 'C语言基础知识'),
('顺序结构', 1, '顺序程序设计'),
('分支结构', 1, 'if-else条件判断'),
('循环结构', 1, 'for/while/do-while循环'),
('数组', NULL, '一维和多维数组'),
('一维数组', 6, '一维数组操作'),
('二维数组', 6, '二维数组操作'),
('函数', NULL, '函数的定义与调用'),
('指针', NULL, '指针高级应用'),
('结构体', NULL, '自定义数据类型'),
('算法', NULL, '常用算法实现'),
('排序算法', 11, '冒泡、快速、归并排序等'),
('搜索算法', 11, '二分查找、深度优先搜索等');

-- 插示：如果需要添加默认管理员账号，请执行以下SQL：
-- INSERT INTO `users` (`username`, `email`, `password_hash`, `role`, `nickname`)
-- VALUES ('admin', 'admin@example.com', '你的密码哈希值', 'admin', '系统管理员');

-- =====================================================
-- 数据库初始化完成！
-- 总计: 20张数据表 + 初始分类数据
-- =====================================================
