#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
推荐系统路由
提供个性化学习推荐和代码分析服务
"""

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.recommendation import RecommendationEngine, CodeAnalyzer

recommendation_bp = Blueprint('recommendation', __name__)


@recommendation_bp.route('/', methods=['GET'])
@login_required
def recommendations_page():
    """推荐页面"""
    return render_template('recommendations.html')


@recommendation_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """获取个性化学习推荐"""
    try:
        recommendations = RecommendationEngine.get_recommendations(current_user.id)
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendation_bp.route('/learning-path', methods=['GET'])
@login_required
def get_learning_path():
    """获取个性化学习路径"""
    try:
        learning_path = RecommendationEngine.get_learning_path(current_user.id)
        return jsonify({
            'success': True,
            'learning_path': learning_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendation_bp.route('/analyze-code', methods=['POST'])
@login_required
def analyze_code():
    """分析代码质量"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({
                'success': False,
                'error': '代码不能为空'
            }), 400
        
        suggestions = RecommendationEngine.analyze_code_quality(code)
        optimization = CodeAnalyzer.get_optimization_suggestions(code)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'optimization': optimization,
            'score': calculate_code_score(suggestions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendation_bp.route('/analyze-error', methods=['POST'])
@login_required
def analyze_error():
    """分析错误信息"""
    try:
        data = request.get_json()
        error_message = data.get('error', '')
        
        if not error_message:
            return jsonify({
                'success': False,
                'error': '错误信息不能为空'
            }), 400
        
        analysis = CodeAnalyzer.analyze_error(error_message)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommendation_bp.route('/progress', methods=['GET'])
@login_required
def get_progress():
    """获取学习进度统计"""
    try:
        from app.models import Submission, Problem
        
        # 获取用户的所有提交
        submissions = Submission.get_by_user(current_user.id)
        
        # 统计信息
        total_submissions = len(submissions)
        accepted = sum(1 for s in submissions if s.status == 'accepted')
        wrong_answer = sum(1 for s in submissions if s.status == 'wrong_answer')
        runtime_error = sum(1 for s in submissions if s.status == 'runtime_error')
        compile_error = sum(1 for s in submissions if s.status == 'compile_error')
        
        # 获取解决的题目
        solved_problems = set()
        for submission in submissions:
            if submission.status == 'accepted':
                solved_problems.add(submission.problem_id)
        
        # 获取总题目数
        all_problems = Problem.get_all()
        total_problems = len(all_problems)
        
        # 计算知识点掌握情况
        topic_stats = RecommendationEngine.analyze_user_progress(current_user.id)
        
        return jsonify({
            'success': True,
            'progress': {
                'total_submissions': total_submissions,
                'accepted': accepted,
                'wrong_answer': wrong_answer,
                'runtime_error': runtime_error,
                'compile_error': compile_error,
                'solved_problems': len(solved_problems),
                'total_problems': total_problems,
                'completion_rate': len(solved_problems) / total_problems if total_problems > 0 else 0,
                'topic_stats': topic_stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def calculate_code_score(suggestions):
    """计算代码质量分数"""
    if not suggestions:
        return 100
    
    # 根据建议的严重程度扣分
    score = 100
    for suggestion in suggestions:
        severity = suggestion.get('severity', 'low')
        if severity == 'high':
            score -= 15
        elif severity == 'medium':
            score -= 10
        else:
            score -= 5
    
    return max(0, score)
