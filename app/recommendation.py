#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能推荐系统
根据用户的学习进度、历史问题和代码提交提供个性化推荐
"""

from datetime import datetime, timedelta
from collections import Counter
import re

class RecommendationEngine:
    """推荐引擎"""

    _topics_cache = None
    _resources_cache = None
    _descriptions_cache = None
    _time_cache = None

    @classmethod
    def _get_db_connection(cls):
        from flask import current_app
        db = current_app.config.get('DATABASE')
        if db:
            conn = db.get_connection()
            return conn, db
        return None, None

    @classmethod
    def _is_mysql(cls, db):
        from app.mysql_database import MySQLDatabase
        return isinstance(db, MySQLDatabase)

    @classmethod
    def get_knowledge_topics(cls):
        if cls._topics_cache is not None:
            return cls._topics_cache

        topics = {}
        conn, db = cls._get_db_connection()
        if conn and db:
            try:
                is_mysql = cls._is_mysql(db)
                cursor = conn.cursor(dictionary=True) if is_mysql else conn.cursor()
                cursor.execute('SELECT category, keyword, description, estimated_time FROM knowledge_topics WHERE is_active = 1 ORDER BY category, sort_order')
                rows = cursor.fetchall()
                for row in rows:
                    if is_mysql:
                        cat = row['category']
                        keyword = row['keyword']
                        desc = row['description']
                        est_time = row['estimated_time']
                    else:
                        cat = row['category']
                        keyword = row['keyword']
                        desc = row['description']
                        est_time = row['estimated_time']
                    if cat not in topics:
                        topics[cat] = []
                    topics[cat].append(keyword)
                    if not hasattr(cls, '_desc_temp'):
                        cls._desc_temp = {}
                        cls._time_temp = {}
                    cls._desc_temp[cat] = desc
                    cls._time_temp[cat] = est_time
                cursor.close()
                cls._topics_cache = topics
                if hasattr(cls, '_desc_temp'):
                    cls._descriptions_cache = cls._desc_temp
                    cls._time_cache = cls._time_temp
                    del cls._desc_temp
                    del cls._time_temp
            except Exception as e:
                print(f'[WARN] Failed to load knowledge topics from DB: {e}')
                topics = cls._get_default_topics()
                cls._topics_cache = topics
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        else:
            topics = cls._get_default_topics()
            cls._topics_cache = topics

        return cls._topics_cache

    @classmethod
    def _get_default_topics(cls):
        return {
            '基础语法': ['Hello World', '变量', '数据类型', '运算符', '输入输出'],
            '控制结构': ['循环', '条件语句', 'switch', 'break', 'continue'],
            '函数': ['函数定义', '参数传递', '递归', '函数重载'],
            '数组和指针': ['数组', '指针', '引用', '动态内存'],
            '面向对象': ['类', '继承', '多态', '封装', '构造函数', '析构函数'],
            'STL': ['vector', 'map', 'set', 'stack', 'queue', '迭代器'],
            '高级特性': ['模板', '异常处理', '文件操作', '命名空间', 'lambda'],
            '数据结构': ['链表', '栈和队列', '二叉树', '哈希表', '图'],
            '算法': ['排序', '查找', '递归', '动态规划', '贪心算法']
        }

    @classmethod
    def get_resources(cls):
        if cls._resources_cache is not None:
            return cls._resources_cache

        resources = {}
        conn, db = cls._get_db_connection()
        if conn and db:
            try:
                is_mysql = cls._is_mysql(db)
                cursor = conn.cursor(dictionary=True) if is_mysql else conn.cursor()
                cursor.execute('SELECT category, resource_type, title, description FROM learning_resources WHERE is_active = 1 ORDER BY category, sort_order')
                rows = cursor.fetchall()
                for row in rows:
                    if is_mysql:
                        cat = row['category']
                        rtype = row['resource_type']
                        title = row['title']
                        desc = row['description']
                    else:
                        cat = row['category']
                        rtype = row['resource_type']
                        title = row['title']
                        desc = row['description']
                    if cat not in resources:
                        resources[cat] = []
                    resources[cat].append({
                        'type': rtype,
                        'title': title,
                        'description': desc
                    })
                cursor.close()
                cls._resources_cache = resources
            except Exception as e:
                print(f'[WARN] Failed to load learning resources from DB: {e}')
                resources = cls._get_default_resources()
                cls._resources_cache = resources
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        else:
            resources = cls._get_default_resources()
            cls._resources_cache = resources

        return cls._resources_cache

    @classmethod
    def _get_default_resources(cls):
        return {
            '基础语法': [
                {'type': 'course', 'title': 'C++基础入门', 'description': '学习C++基本语法和概念'},
                {'type': 'practice', 'title': '基础练习题', 'description': '变量、数据类型和运算符练习'}
            ],
            '控制结构': [
                {'type': 'course', 'title': '流程控制', 'description': '掌握if、for、while等控制语句'},
                {'type': 'practice', 'title': '循环练习', 'description': '各种循环结构的练习题'}
            ],
            '函数': [
                {'type': 'course', 'title': '函数与递归', 'description': '函数定义、调用和递归思想'},
                {'type': 'practice', 'title': '函数练习题', 'description': '函数定义和递归算法练习'}
            ],
            '数组和指针': [
                {'type': 'course', 'title': '指针与内存', 'description': '深入理解指针和内存管理'},
                {'type': 'practice', 'title': '指针练习', 'description': '指针操作和动态内存分配'}
            ],
            '面向对象': [
                {'type': 'course', 'title': '面向对象编程', 'description': '类、对象、继承和多态'},
                {'type': 'practice', 'title': 'OOP练习', 'description': '类和对象的实践练习'}
            ],
            'STL': [
                {'type': 'course', 'title': 'STL标准库', 'description': '掌握vector、map等容器'},
                {'type': 'practice', 'title': 'STL练习', 'description': 'STL容器的使用练习'}
            ],
            '高级特性': [
                {'type': 'course', 'title': 'C++高级特性', 'description': '模板、异常、文件操作'},
                {'type': 'practice', 'title': '高级练习', 'description': '模板和异常处理练习'}
            ],
            '数据结构': [
                {'type': 'course', 'title': '数据结构基础', 'description': '链表、栈、队列、树'},
                {'type': 'practice', 'title': '数据结构练习', 'description': '实现各种数据结构'}
            ],
            '算法': [
                {'type': 'course', 'title': '算法基础', 'description': '排序、查找、递归、DP'},
                {'type': 'practice', 'title': '算法练习', 'description': '经典算法题目练习'}
            ]
        }

    @classmethod
    def invalidate_cache(cls):
        cls._topics_cache = None
        cls._resources_cache = None
        cls._descriptions_cache = None
        cls._time_cache = None
    
    @classmethod
    def analyze_user_progress(cls, user_id):
        """分析用户学习进度"""
        from flask import current_app
        from app.models import Submission, AIConversation, Problem
        
        # 获取用户的所有提交记录
        submissions = Submission.get_by_user(user_id)
        
        # 获取用户的AI对话历史
        conversations = AIConversation.get_by_user(user_id)
        
        # 统计知识点掌握情况
        topic_stats = {topic: {'attempted': 0, 'solved': 0, 'questions': []} 
                      for topic in cls.get_knowledge_topics()}
        
        # 分析提交记录
        for submission in submissions:
            problem = Problem.get_by_id(submission.problem_id)
            if problem:
                # 从题目标题和描述中提取知识点
                problem_text = f"{problem.title} {problem.description}"
                for topic, keywords in cls.get_knowledge_topics().items():
                    for keyword in keywords:
                        if keyword in problem_text:
                            topic_stats[topic]['attempted'] += 1
                            if submission.status == 'AC':
                                topic_stats[topic]['solved'] += 1
                            break
        
        # 分析AI对话历史
        for conversation in conversations:
            question = conversation.question
            for topic, keywords in cls.get_knowledge_topics().items():
                for keyword in keywords:
                    if keyword in question:
                        topic_stats[topic]['questions'].append(question)
                        break
        
        return topic_stats
    
    @classmethod
    def get_weak_topics(cls, user_id):
        """获取用户的薄弱知识点"""
        topic_stats = cls.analyze_user_progress(user_id)
        
        weak_topics = []
        for topic, stats in topic_stats.items():
            attempted = stats['attempted']
            solved = stats['solved']
            
            # 如果有尝试但未完全掌握，或者经常提问
            if attempted > 0:
                success_rate = solved / attempted if attempted > 0 else 0
                if success_rate < 0.7:  # 成功率低于70%
                    weak_topics.append({
                        'topic': topic,
                        'success_rate': success_rate,
                        'attempted': attempted,
                        'solved': solved,
                        'questions_count': len(stats['questions'])
                    })
            elif len(stats['questions']) > 2:  # 经常提问但没有尝试
                weak_topics.append({
                    'topic': topic,
                    'success_rate': 0,
                    'attempted': 0,
                    'solved': 0,
                    'questions_count': len(stats['questions'])
                })
        
        # 按需要改进的程度排序
        weak_topics.sort(key=lambda x: (x['success_rate'], -x['questions_count']))
        return weak_topics[:5]  # 返回前5个薄弱点
    
    @classmethod
    def get_recommendations(cls, user_id):
        """获取个性化推荐"""
        weak_topics = cls.get_weak_topics(user_id)
        
        recommendations = []
        for weak_topic in weak_topics:
            topic_name = weak_topic['topic']
            if topic_name in cls.get_resources():
                resources = cls.get_resources()[topic_name]
                recommendations.append({
                    'topic': topic_name,
                    'reason': cls._generate_reason(weak_topic),
                    'resources': resources,
                    'priority': cls._calculate_priority(weak_topic)
                })
        
        # 如果没有薄弱点，推荐进阶内容
        if not recommendations:
            recommendations = cls._get_advanced_recommendations()
        
        return recommendations
    
    @classmethod
    def _generate_reason(cls, weak_topic):
        """生成推荐理由"""
        if weak_topic['attempted'] > 0:
            success_rate = weak_topic['success_rate'] * 100
            return f"该知识点尝试{weak_topic['attempted']}次，成功率{success_rate:.1f}%，建议加强练习"
        else:
            return f"对该知识点提问{weak_topic['questions_count']}次，建议系统学习"
    
    @classmethod
    def _calculate_priority(cls, weak_topic):
        """计算推荐优先级"""
        if weak_topic['attempted'] > 0:
            return int((1 - weak_topic['success_rate']) * 100)
        else:
            return min(weak_topic['questions_count'] * 20, 100)
    
    @classmethod
    def _get_advanced_recommendations(cls):
        """获取进阶推荐"""
        return [
            {
                'topic': '算法优化',
                'reason': '基础扎实，可以学习更高效的算法',
                'resources': [
                    {'type': 'course', 'title': '高级算法', 'description': '学习高级数据结构和算法'},
                    {'type': 'practice', 'title': '算法挑战', 'description': '高难度算法题目'}
                ],
                'priority': 80
            },
            {
                'topic': '项目实战',
                'reason': '理论知识丰富，建议进行项目实践',
                'resources': [
                    {'type': 'project', 'title': '综合项目', 'description': '完成一个完整的C++项目'},
                    {'type': 'practice', 'title': '实战练习', 'description': '实际应用场景的编程练习'}
                ],
                'priority': 70
            }
        ]
    
    @classmethod
    def analyze_code_quality(cls, code):
        """分析代码质量并提供改进建议"""
        suggestions = []
        
        # 检查代码风格
        if len(code) > 0:
            # 检查缩进
            if '\t' in code:
                suggestions.append({
                    'type': 'style',
                    'issue': '使用Tab缩进',
                    'suggestion': '建议使用4个空格代替Tab进行缩进',
                    'severity': 'low'
                })
            
            # 检查行长度
            lines = code.split('\n')
            long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
            if long_lines:
                suggestions.append({
                    'type': 'style',
                    'issue': f'第{long_lines[:3]}行过长',
                    'suggestion': '建议每行代码不超过120个字符',
                    'severity': 'low'
                })
            
            # 检查命名规范
            if re.search(r'int [a-z]_[a-z]', code):
                suggestions.append({
                    'type': 'style',
                    'issue': '变量命名可能不符合规范',
                    'suggestion': '建议使用驼峰命名法或下划线命名法',
                    'severity': 'low'
                })
            
            # 检查内存管理
            if 'new ' in code and 'delete' not in code:
                suggestions.append({
                    'type': 'memory',
                    'issue': '可能存在内存泄漏',
                    'suggestion': '使用new分配的内存需要使用delete释放，建议使用智能指针',
                    'severity': 'high'
                })
            
            # 检查数组越界
            if re.search(r'\[.*\]', code) and 'at(' not in code and 'size()' not in code.lower():
                suggestions.append({
                    'type': 'safety',
                    'issue': '可能存在数组越界风险',
                    'suggestion': '建议添加边界检查或使用STL容器的at()方法',
                    'severity': 'medium'
                })
            
            # 检查未初始化变量
            if re.search(r'int \w+;', code) and not re.search(r'int \w+ = ', code):
                suggestions.append({
                    'type': 'safety',
                    'issue': '存在未初始化的变量',
                    'suggestion': '建议初始化所有变量，避免使用未定义的值',
                    'severity': 'medium'
                })
            
            # 检查魔法数字
            magic_numbers = re.findall(r'[^\w](\d{2,})[^\w]', code)
            if magic_numbers:
                suggestions.append({
                    'type': 'maintainability',
                    'issue': '代码中存在魔法数字',
                    'suggestion': '建议将常量定义为const变量或宏',
                    'severity': 'low'
                })
        
        return suggestions
    
    @classmethod
    def get_learning_path(cls, user_id):
        """获取个性化学习路径"""
        weak_topics = cls.get_weak_topics(user_id)
        
        # 构建学习路径
        learning_path = []
        for i, topic_info in enumerate(weak_topics[:3], 1):
            topic = topic_info['topic']
            learning_path.append({
                'step': i,
                'topic': topic,
                'description': cls._get_topic_description(topic),
                'estimated_time': cls._estimate_learning_time(topic),
                'resources': cls.get_resources().get(topic, [])
            })
        
        return learning_path
    
    @classmethod
    def _get_topic_description(cls, topic):
        if cls._descriptions_cache is not None and topic in cls._descriptions_cache:
            return cls._descriptions_cache[topic]
        descriptions = {
            '基础语法': '掌握C++的基本语法，包括变量、数据类型、运算符等',
            '控制结构': '学习条件语句和循环语句，控制程序执行流程',
            '函数': '理解函数的定义、调用、参数传递和递归',
            '数组和指针': '深入理解数组和指针，掌握内存管理',
            '面向对象': '学习类、对象、继承、多态等OOP概念',
            'STL': '掌握C++标准模板库的使用',
            '高级特性': '学习模板、异常处理、文件操作等高级特性',
            '数据结构': '掌握常用数据结构的实现和应用',
            '算法': '学习常用算法，提高编程能力'
        }
        return descriptions.get(topic, f'学习{topic}相关知识')
    
    @classmethod
    def _estimate_learning_time(cls, topic):
        if cls._time_cache is not None and topic in cls._time_cache:
            return cls._time_cache[topic]
        time_estimates = {
            '基础语法': '2-3天',
            '控制结构': '3-5天',
            '函数': '5-7天',
            '数组和指针': '7-10天',
            '面向对象': '10-14天',
            'STL': '7-10天',
            '高级特性': '10-14天',
            '数据结构': '14-21天',
            '算法': '21-30天'
        }
        return time_estimates.get(topic, '7-10天')


class CodeAnalyzer:
    """代码分析器"""

    _errors_cache = None

    @classmethod
    def _get_db_connection(cls):
        from flask import current_app
        db = current_app.config.get('DATABASE')
        if db:
            conn = db.get_connection()
            return conn, db
        return None, None

    @classmethod
    def _is_mysql(cls, db):
        from app.mysql_database import MySQLDatabase
        return isinstance(db, MySQLDatabase)

    @classmethod
    def get_common_errors(cls):
        if cls._errors_cache is not None:
            return cls._errors_cache

        errors = {}
        conn, db = cls._get_db_connection()
        if conn and db:
            try:
                import json
                is_mysql = cls._is_mysql(db)
                cursor = conn.cursor(dictionary=True) if is_mysql else conn.cursor()
                cursor.execute('SELECT error_type, pattern, cause, solutions FROM common_errors WHERE is_active = 1 ORDER BY sort_order')
                rows = cursor.fetchall()
                for row in rows:
                    if is_mysql:
                        etype = row['error_type']
                        pattern = row['pattern']
                        cause = row['cause']
                        solutions = row['solutions']
                    else:
                        etype = row['error_type']
                        pattern = row['pattern']
                        cause = row['cause']
                        solutions = row['solutions']
                    errors[etype] = {
                        'pattern': pattern,
                        'cause': cause,
                        'solutions': json.loads(solutions) if isinstance(solutions, str) else solutions
                    }
                cursor.close()
                cls._errors_cache = errors
            except Exception as e:
                print(f'[WARN] Failed to load common errors from DB: {e}')
                errors = cls._get_default_errors()
                cls._errors_cache = errors
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        else:
            errors = cls._get_default_errors()
            cls._errors_cache = errors

        return cls._errors_cache

    @classmethod
    def _get_default_errors(cls):
        return {
            'segmentation fault': {
                'pattern': r'Segmentation fault|段错误',
                'cause': '访问了非法内存地址',
                'solutions': [
                    '检查指针是否初始化',
                    '确保不要访问已释放的内存',
                    '检查数组下标是否越界',
                    '使用调试器定位问题'
                ]
            },
            'memory leak': {
                'pattern': r'memory leak|内存泄漏',
                'cause': '动态分配的内存未释放',
                'solutions': [
                    '使用智能指针管理内存',
                    '确保每个new都有对应的delete',
                    '使用RAII模式',
                    '使用valgrind检测内存泄漏'
                ]
            },
            'undefined reference': {
                'pattern': r'undefined reference|未定义引用',
                'cause': '函数声明但未定义，或缺少库文件',
                'solutions': [
                    '检查函数是否有定义',
                    '确保所有源文件都被编译',
                    '检查链接的库文件',
                    '检查函数签名是否匹配'
                ]
            },
            'array bounds': {
                'pattern': r'array subscript|数组越界',
                'cause': '访问了数组范围之外的元素',
                'solutions': [
                    '检查数组下标范围',
                    '使用STL容器的at()方法',
                    '添加边界检查',
                    '考虑使用动态数组'
                ]
            }
        }

    @classmethod
    def invalidate_cache(cls):
        cls._errors_cache = None
    
    @classmethod
    def analyze_error(cls, error_message):
        """分析错误信息并提供解决方案"""
        error_message = error_message.lower()
        
        for error_type, error_info in cls.get_common_errors().items():
            if re.search(error_info['pattern'], error_message, re.IGNORECASE):
                return {
                    'error_type': error_type,
                    'cause': error_info['cause'],
                    'solutions': error_info['solutions']
                }
        
        return None
    
    @classmethod
    def get_optimization_suggestions(cls, code):
        """获取代码优化建议"""
        suggestions = []
        
        # 检查可以使用STL的地方
        if re.search(r'for\s*\(\s*int\s+\w+\s*=', code) and '++' in code:
            suggestions.append({
                'type': 'modernization',
                'suggestion': '可以使用范围for循环或STL算法简化代码',
                'example': 'for (auto& elem : container) { ... }'
            })
        
        # 检查可以使用auto的地方
        if 'std::vector' in code or 'std::map' in code:
            suggestions.append({
                'type': 'modernization',
                'suggestion': '使用auto关键字简化类型声明',
                'example': 'auto it = vec.begin();'
            })
        
        # 检查可以使用智能指针的地方
        if 'new ' in code:
            suggestions.append({
                'type': 'safety',
                'suggestion': '考虑使用智能指针代替原始指针',
                'example': 'std::unique_ptr<Type> ptr = std::make_unique<Type>();'
            })
        
        # 检查可以使用constexpr的地方
        if re.search(r'const int \w+ = \d+;', code):
            suggestions.append({
                'type': 'performance',
                'suggestion': '使用constexpr代替const进行编译期计算',
                'example': 'constexpr int size = 100;'
            })
        
        return suggestions
