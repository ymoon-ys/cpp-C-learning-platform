from typing import List, Optional
from flask import current_app
from app.models import LearningProgress


class LearningProgressService:
    """学习进度服务类"""

    @staticmethod
    def record_lesson_access(user_id: int, lesson_id: int, course_id: int, chapter_id: int) -> LearningProgress:
        """记录课时访问（开始学习）"""
        return LearningProgress.update_progress(
            user_id=user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            lesson_id=lesson_id,
            progress=0,
            completed=False
        )

    @staticmethod
    def complete_lesson(user_id: int, lesson_id: int, course_id: int, chapter_id: int) -> LearningProgress:
        """完成课时学习"""
        return LearningProgress.update_progress(
            user_id=user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            lesson_id=lesson_id,
            progress=100,
            completed=True
        )

    @staticmethod
    def get_user_course_progress(user_id: int, course_id: int) -> dict:
        """获取用户课程学习进度统计"""
        progress_list = LearningProgress.get_by_user_and_course(user_id, course_id)
        
        total = len(progress_list)
        completed = sum(1 for p in progress_list if p.completed)
        
        return {
            'total': total,
            'completed': completed,
            'percentage': round((completed / total * 100) if total > 0 else 0, 1)
        }

    @staticmethod
    def is_lesson_completed(user_id: int, lesson_id: int) -> bool:
        """检查课时是否已完成"""
        progress = LearningProgress.get_by_user_and_lesson(user_id, lesson_id)
        return progress.completed if progress else False

    @staticmethod
    def get_user_learning_stats(user_id: int) -> dict:
        """获取用户学习统计"""
        all_progress = LearningProgress.get_by_user(user_id)
        
        total_lessons = len(all_progress)
        completed_lessons = sum(1 for p in all_progress if p.completed)
        
        courses = set(p.course_id for p in all_progress if p.course_id)
        
        return {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'total_courses': len(courses),
            'completion_rate': round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0, 1)
        }
