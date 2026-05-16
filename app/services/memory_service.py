import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class MemoryService:
    """
    AI助手记忆系统服务

    记忆类型:
    - knowledge: 知识点掌握情况（如"已掌握指针基础"）
    - weakness: 薄弱环节（如"经常忘记delete动态内存"）
    - preference: 学习偏好（如"喜欢通过代码示例学习"）
    - mistake: 常见错误模式（如"循环边界条件经常出错"）
    - progress: 学习进度标记（如"已完成数组章节"）
    - note: 个人笔记/要点（如"sort函数需要#include <algorithm>"）
    """

    MEMORY_TYPES = ['knowledge', 'weakness', 'preference', 'mistake', 'progress', 'note']

    MEMORY_TYPE_LABELS = {
        'knowledge': '知识点',
        'weakness': '薄弱环节',
        'preference': '学习偏好',
        'mistake': '常见错误',
        'progress': '学习进度',
        'note': '个人笔记'
    }

    def __init__(self, db_connection_func):
        self.get_db = db_connection_func

    def init_tables(self):
        conn = self.get_db()
        if not conn:
            logger.error("Cannot connect to database for memory table init")
            return

        try:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_memory (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                memory_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                source_session_id INT DEFAULT NULL,
                source_message_id INT DEFAULT NULL,
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
                FULLTEXT INDEX ft_content (content)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI助手记忆表'
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_memory_summary (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL UNIQUE,
                summary TEXT,
                last_memory_count INT DEFAULT 0,
                last_summary_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI记忆摘要表'
            ''')

            conn.commit()
            logger.info("AI Memory tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory tables: {str(e)}")
        finally:
            conn.close()

    def add_memory(self, user_id: int, memory_type: str, content: str,
                   source_session_id: int = None, importance: int = 5,
                   tags: List[str] = None) -> Optional[int]:
        if memory_type not in self.MEMORY_TYPES:
            logger.warning(f"Invalid memory type: {memory_type}")
            return None

        conn = self.get_db()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, access_count FROM ai_memory
            WHERE user_id = %s AND content = %s AND is_active = 1
            LIMIT 1
            ''', (user_id, content.strip()))

            existing = cursor.fetchone()
            if existing:
                cursor.execute('''
                UPDATE ai_memory
                SET importance = GREATEST(importance, %s),
                    access_count = access_count + 1,
                    updated_at = NOW()
                WHERE id = %s
                ''', (importance, existing[0]))
                conn.commit()
                return existing[0]

            tags_json = json.dumps(tags) if tags else None

            cursor.execute('''
            INSERT INTO ai_memory (user_id, memory_type, content, source_session_id, importance, tags)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, memory_type, content.strip(), source_session_id, importance, tags_json))

            conn.commit()
            memory_id = cursor.lastrowid
            logger.info(f"Added memory for user {user_id}: [{memory_type}] {content[:50]}...")
            return memory_id

        except Exception as e:
            logger.error(f"Failed to add memory: {str(e)}")
            return None
        finally:
            conn.close()

    def get_memories(self, user_id: int, memory_type: str = None,
                     limit: int = 50, active_only: bool = True) -> List[Dict]:
        conn = self.get_db()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)

            query = '''
            SELECT id, user_id, memory_type, content, source_session_id,
                   importance, access_count, tags, is_active, created_at, updated_at
            FROM ai_memory
            WHERE user_id = %s
            '''
            params = [user_id]

            if memory_type:
                query += ' AND memory_type = %s'
                params.append(memory_type)

            if active_only:
                query += ' AND is_active = 1'

            query += ' ORDER BY importance DESC, updated_at DESC LIMIT %s'
            params.append(limit)

            cursor.execute(query, params)

            memories = []
            for row in cursor.fetchall():
                memory = {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'memory_type': row['memory_type'],
                    'type_label': self.MEMORY_TYPE_LABELS.get(row['memory_type'], row['memory_type']),
                    'content': row['content'],
                    'source_session_id': row['source_session_id'],
                    'importance': row['importance'],
                    'access_count': row['access_count'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'is_active': bool(row['is_active']),
                    'created_at': str(row['created_at']),
                    'updated_at': str(row['updated_at'])
                }
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"Failed to get memories: {str(e)}")
            return []
        finally:
            conn.close()

    def search_memories(self, user_id: int, keyword: str, limit: int = 20) -> List[Dict]:
        if not keyword or len(keyword) < 2:
            return []

        conn = self.get_db()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)

            search_term = f'%{keyword}%'

            cursor.execute('''
            SELECT id, user_id, memory_type, content, importance, access_count,
                   tags, is_active, created_at, updated_at
            FROM ai_memory
            WHERE user_id = %s AND is_active = 1 AND content LIKE %s
            ORDER BY importance DESC, updated_at DESC
            LIMIT %s
            ''', (user_id, search_term, limit))

            memories = []
            for row in cursor.fetchall():
                memory = {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'memory_type': row['memory_type'],
                    'type_label': self.MEMORY_TYPE_LABELS.get(row['memory_type'], row['memory_type']),
                    'content': row['content'],
                    'importance': row['importance'],
                    'access_count': row['access_count'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'created_at': str(row['created_at']),
                    'updated_at': str(row['updated_at'])
                }
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []
        finally:
            conn.close()

    def delete_memory(self, user_id: int, memory_id: int) -> bool:
        conn = self.get_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM ai_memory WHERE id = %s AND user_id = %s
            ''', (memory_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete memory: {str(e)}")
            return False
        finally:
            conn.close()

    def deactivate_memory(self, user_id: int, memory_id: int) -> bool:
        conn = self.get_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE ai_memory SET is_active = 0 WHERE id = %s AND user_id = %s
            ''', (memory_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to deactivate memory: {str(e)}")
            return False
        finally:
            conn.close()

    def get_memory_context_for_prompt(self, user_id: int, current_question: str = '') -> str:
        """
        获取与当前问题相关的记忆，构建注入到system prompt的上下文
        """
        memories = self.get_memories(user_id, limit=30, active_only=True)

        if not memories:
            return ''

        relevant_memories = []
        if current_question:
            question_lower = current_question.lower()
            for m in memories:
                content_lower = m['content'].lower()
                score = 0
                for word in question_lower.split():
                    if len(word) > 1 and word in content_lower:
                        score += 1
                if score > 0:
                    m['_relevance'] = score
                    relevant_memories.append(m)

            relevant_memories.sort(key=lambda x: x.get('_relevance', 0), reverse=True)
            relevant_memories = relevant_memories[:10]

        if not relevant_memories:
            relevant_memories = memories[:8]

        context_parts = []
        type_groups: Dict[str, List] = {}
        for m in relevant_memories:
            mt = m['memory_type']
            if mt not in type_groups:
                type_groups[mt] = []
            type_groups[mt].append(m)

        for mt in ['weakness', 'mistake', 'knowledge', 'preference', 'progress', 'note']:
            if mt in type_groups:
                label = self.MEMORY_TYPE_LABELS.get(mt, mt)
                items = type_groups[mt]
                context_parts.append(f"### {label}")
                for item in items[:5]:
                    context_parts.append(f"- {item['content']}")

        if context_parts:
            return "\n\n## 关于这位学生的记忆（请据此个性化回答）\n\n" + "\n".join(context_parts)
        return ''

    def extract_memories_from_conversation(self, user_id: int, user_message: str,
                                           ai_response: str, session_id: int = None) -> List[int]:
        """
        从对话中提取值得记忆的信息
        使用规则匹配 + 关键词提取，无需额外调用AI模型
        """
        added_ids = []

        memories_to_add = []

        self._extract_knowledge_memories(user_message, ai_response, memories_to_add)
        self._extract_mistake_memories(user_message, ai_response, memories_to_add)
        self._extract_weakness_memories(user_message, ai_response, memories_to_add)
        self._extract_preference_memories(user_message, memories_to_add)
        self._extract_progress_memories(user_message, ai_response, memories_to_add)
        self._extract_note_memories(user_message, ai_response, memories_to_add)

        for mem in memories_to_add:
            mem_id = self.add_memory(
                user_id=user_id,
                memory_type=mem['type'],
                content=mem['content'],
                source_session_id=session_id,
                importance=mem.get('importance', 5),
                tags=mem.get('tags')
            )
            if mem_id:
                added_ids.append(mem_id)

        return added_ids

    def _extract_knowledge_memories(self, user_message: str, ai_response: str, memories: list):
        knowledge_patterns = [
            (r'我(?:已经|已|现在)(?:学会了|掌握了|理解了|弄懂了|搞懂了)(.+?)[。，！？]', 'knowledge', 7),
            (r'我(?:知道|了解|明白)(?:了|啦)?(.+?)(?:的|这个)(?:概念|原理|用法|方法|规则)', 'knowledge', 6),
            (r'(?:终于|总算)(?:搞懂|理解|明白|学会)(?:了|啦)?(.+?)[。，！？]', 'knowledge', 7),
        ]

        for pattern, mem_type, importance in knowledge_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                content = match.strip()
                if len(content) > 3:
                    memories.append({
                        'type': mem_type,
                        'content': f"已掌握: {content}",
                        'importance': importance,
                        'tags': ['auto-extract', 'knowledge']
                    })

        concept_patterns = [
            r'##\s*(.+?的(?:定义|概念|原理|用法))',
            r'###\s*(.+?(?:基础|入门|核心|要点|关键))',
        ]

        for pattern in concept_patterns:
            matches = re.findall(pattern, ai_response)
            for match in matches:
                content = match.strip()
                if len(content) > 3:
                    memories.append({
                        'type': 'knowledge',
                        'content': f"学习过: {content}",
                        'importance': 4,
                        'tags': ['auto-extract', 'topic']
                    })

    def _extract_mistake_memories(self, user_message: str, ai_response: str, memories: list):
        mistake_indicators = [
            '错误', 'bug', '问题', '不对', '不正确', '有误',
            '编译失败', '运行错误', '段错误', '越界', '泄漏',
            '未定义', '空指针', '溢出', '死循环'
        ]

        has_mistake = any(ind in ai_response for ind in mistake_indicators)

        if has_mistake:
            mistake_patterns = [
                r'(?:错误|问题|bug)[：:]\s*(.+?)(?:\n|$)',
                r'(?:⚠️|❌|🔴)\s*(.+?)(?:\n|$)',
                r'第\d+行[：:]\s*(.+?)(?:\n|$)',
            ]

            for pattern in mistake_patterns:
                matches = re.findall(pattern, ai_response)
                for match in matches:
                    content = match.strip()
                    if 5 < len(content) < 200:
                        memories.append({
                            'type': 'mistake',
                            'content': f"常见错误: {content}",
                            'importance': 6,
                            'tags': ['auto-extract', 'mistake']
                        })
                        break

            if not any(m['type'] == 'mistake' for m in memories):
                user_code_indicators = ['我的代码', '这段代码', '我的程序', '为什么报错', '运行不了']
                if any(ind in user_message for ind in user_code_indicators):
                    memories.append({
                        'type': 'mistake',
                        'content': f"代码调试: {user_message[:100]}",
                        'importance': 4,
                        'tags': ['auto-extract', 'debug']
                    })

    def _extract_weakness_memories(self, user_message: str, ai_response: str, memories: list):
        weakness_indicators = {
            '指针': '指针操作',
            '递归': '递归理解',
            '动态内存': '动态内存管理',
            'new.*delete': '动态内存管理',
            '链表': '链表操作',
            '排序': '排序算法',
            '二叉树': '树结构',
            '模板': '模板编程',
            '继承': '面向对象继承',
            '多态': '多态概念',
            '虚函数': '虚函数机制',
            'stl': 'STL使用',
            '引用': '引用与指针区别',
        }

        user_lower = user_message.lower()
        for pattern, weakness in weakness_indicators.items():
            if re.search(pattern, user_lower):
                existing_weakness = any(
                    m['type'] == 'weakness' and weakness in m['content']
                    for m in memories
                )
                if not existing_weakness:
                    memories.append({
                        'type': 'weakness',
                        'content': f"需要加强: {weakness}",
                        'importance': 5,
                        'tags': ['auto-extract', 'weakness']
                    })

    def _extract_preference_memories(self, user_message: str, memories: list):
        preference_patterns = [
            (r'我(?:比较|更)?喜欢(.+?)(?:的|来|去)?(?:学习|理解|看|写)', 'preference'),
            (r'请(?:用|给|帮)(.+?)(?:方式|方法|例子)', 'preference'),
            (r'能不能(?:用|给)(.+?)(?:解释|说明|举例)', 'preference'),
        ]

        for pattern, mem_type in preference_patterns:
            matches = re.findall(pattern, user_message)
            for match in matches:
                content = match.strip()
                if len(content) > 2:
                    memories.append({
                        'type': mem_type,
                        'content': f"学习偏好: 喜欢{content}方式学习",
                        'importance': 5,
                        'tags': ['auto-extract', 'preference']
                    })

    def _extract_progress_memories(self, user_message: str, ai_response: str, memories: list):
        progress_patterns = [
            (r'我(?:已经|已)(?:学完|完成|做完|做完|刷完|看完)(?:了|啦)?(.+?)[。，！？]', 8),
            (r'我(?:正在|现在在|准备)(?:学|做|看|刷|写)(.+?)[。，！？]', 6),
            (r'第(?:一|二|三|四|五|六|七|八|九|十|\d+)(?:章|节|课|部分)(.+?)(?:学完|完成|做完)', 7),
            (r'我(?:刚|刚刚)(?:学|做|看|写)(?:完|了)(.+?)[。，！？]', 7),
            (r'(?:进入|开始)(?:了|啦)?(.+?)(?:阶段|部分|章节)', 6),
        ]

        for pattern, importance in progress_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                content = match.strip()
                if len(content) > 2:
                    memories.append({
                        'type': 'progress',
                        'content': f"学习进度: {content}",
                        'importance': importance,
                        'tags': ['auto-extract', 'progress']
                    })

        chapter_section = re.findall(r'##\s*(第.+?章.+?)[\s\n]', ai_response)
        for section in chapter_section[:2]:
            memories.append({
                'type': 'progress',
                'content': f"学习进度: 正在学习{section.strip()}",
                'importance': 4,
                'tags': ['auto-extract', 'progress', 'topic']
            })

        ac_indicators = ['通过', 'AC', '正确', '成功', 'accepted']
        if any(ind in user_message for ind in ac_indicators):
            topic_match = re.findall(r'(?:题目|问题|练习|算法)(.+?)(?:通过|AC|正确|成功)', user_message)
            for topic in topic_match:
                memories.append({
                    'type': 'progress',
                    'content': f"学习进度: 已完成{topic.strip()}相关练习",
                    'importance': 7,
                    'tags': ['auto-extract', 'progress', 'practice']
                })

    def _extract_note_memories(self, user_message: str, ai_response: str, memories: list):
        note_patterns = [
            (r'(?:记住|记住啦|记下了|记一下|备忘|注意|重要|关键点|要点)[：:，]?\s*(.+?)[。，！？]', 7),
            (r'(?:这个|这个要|一定要|千万别|别忘记|别忘了)(.+?)(?:容易错|容易忘|重要|关键)', 6),
            (r'(?:tip|提示|技巧|窍门|经验)[：:]\s*(.+?)[。，！？]', 6),
            (r'(?:注意|注意啦|小心|当心)[：:，]?\s*(.+?)[。，！？]', 5),
        ]

        for pattern, importance in note_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                content = match.strip()
                if len(content) > 3:
                    memories.append({
                        'type': 'note',
                        'content': f"个人笔记: {content}",
                        'importance': importance,
                        'tags': ['auto-extract', 'note']
                    })

        ai_note_patterns = [
            r'⚠️\s*(.+?)(?:\n|$)',
            r'💡\s*(.+?)(?:\n|$)',
            r'📌\s*(.+?)(?:\n|$)',
            r'\*\*注意\*\*[：:]\s*(.+?)(?:\n|$)',
            r'\*\*重要\*\*[：:]\s*(.+?)(?:\n|$)',
        ]

        for pattern in ai_note_patterns:
            matches = re.findall(pattern, ai_response)
            for match in matches[:2]:
                content = match.strip()
                if 5 < len(content) < 200:
                    memories.append({
                        'type': 'note',
                        'content': f"知识要点: {content}",
                        'importance': 5,
                        'tags': ['auto-extract', 'note', 'ai-highlight']
                    })

        key_point_patterns = [
            r'###\s*(.+?(?:注意|要点|关键|重点|核心|技巧))',
            r'###\s*(常见(?:错误|陷阱|误区|坑))',
        ]
        for pattern in key_point_patterns:
            matches = re.findall(pattern, ai_response)
            for match in matches[:2]:
                content = match.strip()
                if len(content) > 3:
                    memories.append({
                        'type': 'note',
                        'content': f"知识要点: {content}",
                        'importance': 6,
                        'tags': ['auto-extract', 'note', 'key-point']
                    })

    def get_memory_stats(self, user_id: int) -> Dict[str, Any]:
        conn = self.get_db()
        if not conn:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)

            stats = {
                'total': 0,
                'by_type': {},
                'recent_count': 0
            }

            cursor.execute('''
            SELECT memory_type, COUNT(*) as count, AVG(importance) as avg_importance
            FROM ai_memory
            WHERE user_id = %s AND is_active = 1
            GROUP BY memory_type
            ''', (user_id,))

            for row in cursor.fetchall():
                mt = row['memory_type']
                count = row['count']
                stats['by_type'][mt] = {
                    'count': count,
                    'label': self.MEMORY_TYPE_LABELS.get(mt, mt),
                    'avg_importance': round(float(row['avg_importance']), 1)
                }
                stats['total'] += count

            cursor.execute('''
            SELECT COUNT(*) as count FROM ai_memory
            WHERE user_id = %s AND is_active = 1
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ''', (user_id,))

            result = cursor.fetchone()
            stats['recent_count'] = result['count'] if result else 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get memory stats: {str(e)}")
            return {}
        finally:
            conn.close()

    def update_memory_summary(self, user_id: int) -> bool:
        """
        更新用户的记忆摘要（用于快速了解学生画像）
        """
        memories = self.get_memories(user_id, limit=50, active_only=True)

        if not memories:
            return True

        summary_parts = []

        type_groups: Dict[str, List] = {}
        for m in memories:
            mt = m['memory_type']
            if mt not in type_groups:
                type_groups[mt] = []
            type_groups[mt].append(m)

        if 'knowledge' in type_groups:
            items = [m['content'] for m in type_groups['knowledge'][:10]]
            summary_parts.append(f"已掌握知识: {'; '.join(items)}")

        if 'weakness' in type_groups:
            items = [m['content'] for m in type_groups['weakness'][:5]]
            summary_parts.append(f"薄弱环节: {'; '.join(items)}")

        if 'mistake' in type_groups:
            items = [m['content'] for m in type_groups['mistake'][:5]]
            summary_parts.append(f"常见错误: {'; '.join(items)}")

        if 'preference' in type_groups:
            items = [m['content'] for m in type_groups['preference'][:3]]
            summary_parts.append(f"学习偏好: {'; '.join(items)}")

        summary = '\n'.join(summary_parts)

        conn = self.get_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO ai_memory_summary (user_id, summary, last_memory_count)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE summary = %s, last_memory_count = %s, last_summary_at = NOW()
            ''', (user_id, summary, len(memories), summary, len(memories)))

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update memory summary: {str(e)}")
            return False
        finally:
            conn.close()

    def get_memory_summary(self, user_id: int) -> Optional[str]:
        conn = self.get_db()
        if not conn:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
            SELECT summary FROM ai_memory_summary WHERE user_id = %s
            ''', (user_id,))

            result = cursor.fetchone()
            return result['summary'] if result else None
        except Exception as e:
            logger.error(f"Failed to get memory summary: {str(e)}")
            return None
        finally:
            conn.close()

    def decay_memories(self, user_id: int, days_threshold: int = 30,
                       min_importance: int = 1, decay_amount: int = 1) -> int:
        """
        记忆衰减：长期未被访问的记忆重要性降低
        超过 days_threshold 天未更新的记忆，importance 减去 decay_amount
        低于 min_importance 的记忆被停用
        """
        conn = self.get_db()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()

            cursor.execute('''
            UPDATE ai_memory
            SET importance = GREATEST(%s, importance - %s)
            WHERE user_id = %s AND is_active = 1
            AND updated_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            AND importance > %s
            ''', (min_importance, decay_amount, user_id, days_threshold, min_importance))

            decayed = cursor.rowcount

            cursor.execute('''
            UPDATE ai_memory
            SET is_active = 0
            WHERE user_id = %s AND is_active = 1
            AND importance <= %s
            ''', (user_id, min_importance))

            deactivated = cursor.rowcount
            conn.commit()

            logger.info(f"Memory decay for user {user_id}: {decayed} decayed, {deactivated} deactivated")
            return decayed + deactivated
        except Exception as e:
            logger.error(f"Failed to decay memories: {str(e)}")
            return 0
        finally:
            conn.close()

    def boost_memory_access(self, user_id: int, memory_ids: List[int],
                            boost_importance: int = 1) -> bool:
        """
        记忆强化：被引用的记忆增加 access_count 和 importance
        """
        if not memory_ids:
            return True

        conn = self.get_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            placeholders = ','.join(['%s'] * len(memory_ids))
            cursor.execute(f'''
            UPDATE ai_memory
            SET access_count = access_count + 1,
                importance = LEAST(10, importance + %s),
                updated_at = NOW()
            WHERE user_id = %s AND id IN ({placeholders}) AND is_active = 1
            ''', (boost_importance, user_id, *memory_ids))

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to boost memory access: {str(e)}")
            return False
        finally:
            conn.close()

    def merge_similar_memories(self, user_id: int, similarity_threshold: float = 0.7) -> int:
        """
        合并相似记忆：内容高度重叠的记忆合并为一条
        使用简单的 Jaccard 相似度
        """
        memories = self.get_memories(user_id, limit=100, active_only=True)
        if len(memories) < 2:
            return 0

        merged_count = 0
        to_deactivate = set()

        for i in range(len(memories)):
            if memories[i]['id'] in to_deactivate:
                continue
            for j in range(i + 1, len(memories)):
                if memories[j]['id'] in to_deactivate:
                    continue
                if memories[i]['memory_type'] != memories[j]['memory_type']:
                    continue

                similarity = self._jaccard_similarity(
                    memories[i]['content'], memories[j]['content']
                )

                if similarity >= similarity_threshold:
                    if memories[i]['importance'] >= memories[j]['importance']:
                        to_deactivate.add(memories[j]['id'])
                        self.boost_memory_access(user_id, [memories[i]['id']])
                    else:
                        to_deactivate.add(memories[i]['id'])
                        self.boost_memory_access(user_id, [memories[j]['id']])
                    merged_count += 1

        for mid in to_deactivate:
            self.deactivate_memory(user_id, mid)

        if merged_count > 0:
            logger.info(f"Merged {merged_count} similar memories for user {user_id}")
        return merged_count

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的 Jaccard 相似度"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union)

    def evolve_memories(self, user_id: int) -> Dict[str, Any]:
        """
        记忆进化：执行衰减 + 合并 + 摘要更新
        """
        decay_result = self.decay_memories(user_id)
        merge_result = self.merge_similar_memories(user_id)
        self.update_memory_summary(user_id)

        stats = self.get_memory_stats(user_id)

        return {
            'decayed': decay_result,
            'merged': merge_result,
            'stats': stats
        }

    def get_radar_chart_data(self, user_id: int) -> Dict[str, Any]:
        """
        生成学习能力雷达图数据
        按记忆类型聚合，计算各维度得分（0-100）
        六个维度：知识掌握、薄弱环节识别、学习偏好明确度、错误反思、学习进度、笔记积累
        """
        memories = self.get_memories(user_id, limit=200, active_only=True)
        stats = self.get_memory_stats(user_id)

        by_type: Dict[str, List] = {}
        for m in memories:
            mt = m['memory_type']
            if mt not in by_type:
                by_type[mt] = []
            by_type[mt].append(m)

        knowledge_count = len(by_type.get('knowledge', []))
        weakness_count = len(by_type.get('weakness', []))
        mistake_count = len(by_type.get('mistake', []))
        preference_count = len(by_type.get('preference', []))
        progress_count = len(by_type.get('progress', []))
        note_count = len(by_type.get('note', []))

        knowledge_score = min(100, knowledge_count * 10)
        if knowledge_count > 0:
            avg_importance = sum(m['importance'] for m in by_type['knowledge']) / knowledge_count
            knowledge_score = min(100, int(knowledge_count * 5 + avg_importance * 8))

        weakness_score = min(100, weakness_count * 15)
        if weakness_count > 0:
            weakness_score = min(100, int(weakness_count * 10 + 30))

        mistake_score = min(100, mistake_count * 12)
        if mistake_count > 0:
            avg_importance = sum(m['importance'] for m in by_type['mistake']) / mistake_count
            mistake_score = min(100, int(mistake_count * 8 + avg_importance * 6))

        preference_score = min(100, preference_count * 20)
        if preference_count > 0:
            preference_score = min(100, int(preference_count * 15 + 40))

        progress_score = min(100, progress_count * 15)
        if progress_count > 0:
            avg_importance = sum(m['importance'] for m in by_type['progress']) / progress_count
            progress_score = min(100, int(progress_count * 10 + avg_importance * 5))

        note_score = min(100, note_count * 12)
        if note_count > 0:
            avg_importance = sum(m['importance'] for m in by_type['note']) / note_count
            note_score = min(100, int(note_count * 8 + avg_importance * 6))

        dimensions = [
            {'name': '知识掌握', 'key': 'knowledge', 'score': knowledge_score,
             'count': knowledge_count, 'description': '已掌握的C++知识点数量和深度'},
            {'name': '薄弱识别', 'key': 'weakness', 'score': weakness_score,
             'count': weakness_count, 'description': '对自身薄弱环节的认知程度'},
            {'name': '错误反思', 'key': 'mistake', 'score': mistake_score,
             'count': mistake_count, 'description': '从错误中总结经验的能力'},
            {'name': '偏好明确', 'key': 'preference', 'score': preference_score,
             'count': preference_count, 'description': '学习方式和偏好的明确程度'},
            {'name': '学习进度', 'key': 'progress', 'score': progress_score,
             'count': progress_count, 'description': '学习路径的推进程度'},
            {'name': '笔记积累', 'key': 'note', 'score': note_score,
             'count': note_count, 'description': '知识要点的记录和积累'},
        ]

        overall_score = sum(d['score'] for d in dimensions) / len(dimensions)

        if overall_score >= 80:
            level = '优秀'
            advice = '学习状态非常好，建议挑战更高难度的内容'
        elif overall_score >= 60:
            level = '良好'
            advice = '学习状态不错，继续保持，注意补强薄弱环节'
        elif overall_score >= 40:
            level = '一般'
            advice = '建议多与AI助手互动，系统会更好地了解你的学习状态'
        else:
            level = '起步'
            advice = '刚开始学习，多提问、多练习，AI会逐渐了解你'

        weakest = min(dimensions, key=lambda d: d['score'])
        strongest = max(dimensions, key=lambda d: d['score'])

        return {
            'dimensions': dimensions,
            'overall_score': round(overall_score, 1),
            'level': level,
            'advice': advice,
            'strongest': strongest,
            'weakest': weakest,
            'total_memories': len(memories),
            'by_type_counts': {
                'knowledge': knowledge_count,
                'weakness': weakness_count,
                'mistake': mistake_count,
                'preference': preference_count,
                'progress': progress_count,
                'note': note_count,
            }
        }
