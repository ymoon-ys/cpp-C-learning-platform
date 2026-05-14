#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社区功能路由 - 贴吧+抖音风格
支持图片上传、嵌套评论、点赞功能
"""

from flask import Blueprint, jsonify, request, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.utils import get_consecutive_learning_days
import os
import json

community_bp = Blueprint('community', __name__)


# ==================== 工具函数 ====================

def save_uploaded_image(file, folder='community'):
    """保存上传的图片"""
    from werkzeug.utils import secure_filename
    
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    if not file or file.filename == '':
        return None
    
    filename = secure_filename(file.filename)
    if not filename:
        return None
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    
    filename = f"{folder}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id}{ext}"
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    return f"/uploads/{folder}/{filename}"


def get_user_info(user_id):
    """获取用户信息"""
    from app.models import User
    user = User.get_by_id(user_id)
    if user:
        return {
            'id': user.id,
            'nickname': user.nickname or user.username,
            'avatar': user.avatar or '/static/default-avatar.png'
        }
    return {'id': user_id, 'nickname': '未知用户', 'avatar': '/static/default-avatar.png'}


# ==================== 讨论区（贴吧风格） ====================

@community_bp.route('/discussions', methods=['GET'])
def get_discussions():
    """获取讨论列表 - 贴吧风格"""
    try:
        db = current_app.db
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 构建查询
        discussions = db.find_all('discussions')
        discussions = sorted(discussions, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 分页
        discussions = discussions[offset:offset+limit]
        
        result = []
        for d in discussions:
            user_info = get_user_info(d.get('user_id'))
            
            # 获取评论数
            replies_count = len(db.find_by_field('replies', 'discussion_id', d.get('id')))
            
            # 检查当前用户是否点赞
            is_liked = False
            if current_user.is_authenticated:
                likes = db.find_by_field('discussion_likes', 'discussion_id', d.get('id'))
                is_liked = any(l.get('user_id') == current_user.id for l in likes)
            
            # 解析图片
            images = []
            if d.get('images'):
                try:
                    images = json.loads(d.get('images'))
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    import logging
                    logging.warning(f"Failed to parse images JSON: {e}")
                    images = []
            
            result.append({
                'id': d.get('id'),
                'title': d.get('title'),
                'content': d.get('content', '')[:200],  # 预览前200字符
                'content_full': d.get('content', ''),
                'images': images,
                'tags': d.get('tags', '').split(',') if d.get('tags') else [],
                'view_count': d.get('view_count', 0),
                'like_count': d.get('like_count', 0),
                'reply_count': replies_count,
                'is_liked': is_liked,
                'created_at': d.get('created_at'),
                'user': user_info
            })
        
        return jsonify({'success': True, 'discussions': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/discussions/<int:discussion_id>', methods=['GET'])
def get_discussion_detail(discussion_id):
    """获取讨论详情 - 包含评论"""
    try:
        db = current_app.db
        
        # 获取讨论
        d = db.find_by_id('discussions', discussion_id)
        if not d:
            return jsonify({'success': False, 'error': '讨论不存在'}), 404
        
        # 增加浏览量
        view_count = (d.get('view_count') or 0) + 1
        db.update('discussions', discussion_id, {'view_count': view_count})
        
        user_info = get_user_info(d.get('user_id'))
        
        # 检查是否点赞
        is_liked = False
        if current_user.is_authenticated:
            likes = db.find_by_field('discussion_likes', 'discussion_id', discussion_id)
            is_liked = any(l.get('user_id') == current_user.id for l in likes)
        
        # 解析图片
        images = []
        if d.get('images'):
            try:
                images = json.loads(d.get('images'))
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                import logging
                logging.warning(f"Failed to parse images JSON: {e}")
                images = []
        
        discussion = {
            'id': d.get('id'),
            'title': d.get('title'),
            'content': d.get('content', ''),
            'images': images,
            'category': d.get('category', 'general'),
            'tags': d.get('tags', '').split(',') if d.get('tags') else [],
            'view_count': view_count,
            'like_count': d.get('like_count', 0),
            'is_liked': is_liked,
            'created_at': d.get('created_at'),
            'user': user_info,
            'is_owner': current_user.is_authenticated and current_user.id == d.get('user_id'),
            'current_user_id': current_user.id if current_user.is_authenticated else None
        }
        
        # 获取评论（抖音风格 - 嵌套回复）
        replies = build_reply_tree(discussion_id)
        
        return jsonify({
            'success': True,
            'discussion': discussion,
            'replies': replies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def build_reply_tree(discussion_id):
    """构建评论树（支持嵌套回复）"""
    db = current_app.db
    
    # 获取所有评论
    all_replies = db.find_by_field('replies', 'discussion_id', discussion_id)
    
    # 按时间排序
    all_replies = sorted(all_replies, key=lambda x: x.get('created_at', ''))
    
    reply_dict = {}
    root_replies = []
    
    # 第一遍：创建所有回复对象
    for r in all_replies:
        user_info = get_user_info(r.get('user_id'))
        
        # 检查是否点赞
        is_liked = False
        if current_user.is_authenticated:
            likes = db.find_by_field('reply_likes', 'reply_id', r.get('id'))
            is_liked = any(l.get('user_id') == current_user.id for l in likes)
        
        reply_obj = {
            'id': r.get('id'),
            'content': r.get('content'),
            'like_count': r.get('like_count', 0),
            'is_liked': is_liked,
            'created_at': r.get('created_at'),
            'user': user_info,
            'parent_id': r.get('parent_id'),
            'is_comment_owner': current_user.is_authenticated and current_user.id == r.get('user_id'),
            'children': []
        }
        reply_dict[r.get('id')] = reply_obj
    
    # 第二遍：构建树形结构
    for r in all_replies:
        reply_obj = reply_dict[r.get('id')]
        parent_id = r.get('parent_id')
        
        if parent_id and parent_id in reply_dict:
            # 如果有父评论，添加到父评论的子列表
            reply_dict[parent_id]['children'].append(reply_obj)
        else:
            # 否则是根评论
            root_replies.append(reply_obj)
    
    return root_replies


@community_bp.route('/discussions', methods=['POST'])
@login_required
def create_discussion():
    """创建讨论 - 支持图片上传"""
    try:
        db = current_app.db
        
        # 获取表单数据
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title:
            return jsonify({'success': False, 'error': '标题不能为空'}), 400
        
        # 处理图片上传
        images = []
        if 'images' in request.files:
            uploaded_files = request.files.getlist('images')
            for file in uploaded_files:
                if file and file.filename:
                    image_path = save_uploaded_image(file, 'community')
                    if image_path:
                        images.append(image_path)
        
        # 保存到数据库
        data = {
            'user_id': current_user.id,
            'course_id': None,  # 社区讨论，没有课程ID
            'title': title,
            'content': content,
            'images': json.dumps(images) if images else '',
            'category': 'general',  # 默认分类
            'tags': '',  # 默认为空
            'view_count': 0,
            'like_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        discussion_id = db.insert('discussions', data)
        
        return jsonify({
            'success': True,
            'message': '发布成功',
            'discussion_id': discussion_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/discussions/<int:discussion_id>/replies', methods=['POST'])
@login_required
def create_reply(discussion_id):
    """创建评论/回复 - 抖音风格支持嵌套"""
    try:
        db = current_app.db
        
        # 检查讨论是否存在
        discussion = db.find_by_id('discussions', discussion_id)
        if not discussion:
            return jsonify({'success': False, 'error': '讨论不存在'}), 404
        
        content = request.form.get('content') or (request.get_json(silent=True) or {}).get('content')
        parent_id = request.form.get('parent_id') or (request.get_json(silent=True) or {}).get('parent_id')
        
        if not content:
            return jsonify({'success': False, 'error': '内容不能为空'}), 400
        
        # 保存评论
        data = {
            'discussion_id': discussion_id,
            'user_id': current_user.id,
            'parent_id': parent_id,
            'content': content,
            'like_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        reply_id = db.insert('replies', data)
        
        return jsonify({
            'success': True,
            'message': '评论成功',
            'reply_id': reply_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 点赞功能 ====================

@community_bp.route('/discussions/<int:discussion_id>/like', methods=['POST'])
@login_required
def like_discussion(discussion_id):
    """点赞/取消点赞讨论"""
    try:
        db = current_app.db
        
        # 检查是否已点赞
        likes = db.find_by_field('discussion_likes', 'discussion_id', discussion_id)
        existing_like = None
        for like in likes:
            if like.get('user_id') == current_user.id:
                existing_like = like
                break
        
        if existing_like:
            # 取消点赞
            db.delete('discussion_likes', existing_like.get('id'))
            
            # 更新点赞数
            discussion = db.find_by_id('discussions', discussion_id)
            if discussion:
                like_count = max(0, (discussion.get('like_count') or 0) - 1)
                db.update('discussions', discussion_id, {'like_count': like_count})
            
            return jsonify({'success': True, 'liked': False, 'like_count': like_count})
        else:
            # 添加点赞
            data = {
                'discussion_id': discussion_id,
                'user_id': current_user.id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            db.insert('discussion_likes', data)
            
            # 更新点赞数
            discussion = db.find_by_id('discussions', discussion_id)
            if discussion:
                like_count = (discussion.get('like_count') or 0) + 1
                db.update('discussions', discussion_id, {'like_count': like_count})
            
            return jsonify({'success': True, 'liked': True, 'like_count': like_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/replies/<int:reply_id>/like', methods=['POST'])
@login_required
def like_reply(reply_id):
    """点赞/取消点赞评论"""
    try:
        db = current_app.db
        
        # 检查是否已点赞
        likes = db.find_by_field('reply_likes', 'reply_id', reply_id)
        existing_like = None
        for like in likes:
            if like.get('user_id') == current_user.id:
                existing_like = like
                break
        
        if existing_like:
            # 取消点赞
            db.delete('reply_likes', existing_like.get('id'))
            
            # 更新点赞数
            reply = db.find_by_id('replies', reply_id)
            if reply:
                like_count = max(0, (reply.get('like_count') or 0) - 1)
                db.update('replies', reply_id, {'like_count': like_count})
            
            return jsonify({'success': True, 'liked': False, 'like_count': like_count})
        else:
            # 添加点赞
            data = {
                'reply_id': reply_id,
                'user_id': current_user.id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            db.insert('reply_likes', data)
            
            # 更新点赞数
            reply = db.find_by_id('replies', reply_id)
            if reply:
                like_count = (reply.get('like_count') or 0) + 1
                db.update('replies', reply_id, {'like_count': like_count})
            
            return jsonify({'success': True, 'liked': True, 'like_count': like_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/replies/<int:reply_id>', methods=['DELETE'])
@login_required
def delete_reply(reply_id):
    """删除评论"""
    try:
        db = current_app.db
        
        # 检查评论是否存在
        reply = db.find_by_id('replies', reply_id)
        if not reply:
            return jsonify({'success': False, 'error': '评论不存在'}), 404
        
        # 检查是否是评论作者
        if reply.get('user_id') != current_user.id:
            return jsonify({'success': False, 'error': '无权删除此评论'}), 403
        
        # 删除评论
        db.delete('replies', reply_id)
        
        # 删除相关的点赞
        likes = db.find_by_field('reply_likes', 'reply_id', reply_id)
        for like in likes:
            db.delete('reply_likes', like.get('id'))
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/discussions/<int:discussion_id>', methods=['DELETE'])
@login_required
def delete_discussion(discussion_id):
    """删除帖子"""
    try:
        db = current_app.db
        
        # 检查帖子是否存在
        discussion = db.find_by_id('discussions', discussion_id)
        if not discussion:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        # 检查是否是帖子作者
        if discussion.get('user_id') != current_user.id:
            return jsonify({'success': False, 'error': '无权删除此帖子'}), 403
        
        # 删除相关回复
        replies = db.find_by_field('replies', 'discussion_id', discussion_id)
        for reply in replies:
            # 删除回复的点赞
            reply_likes = db.find_by_field('reply_likes', 'reply_id', reply.get('id'))
            for like in reply_likes:
                db.delete('reply_likes', like.get('id'))
            # 删除回复
            db.delete('replies', reply.get('id'))
        
        # 删除帖子的点赞
        likes = db.find_by_field('discussion_likes', 'discussion_id', discussion_id)
        for like in likes:
            db.delete('discussion_likes', like.get('id'))
        
        # 删除帖子
        db.delete('discussions', discussion_id)
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 代码分享（简化版） ====================

@community_bp.route('/code-shares', methods=['GET'])
def get_code_shares():
    """获取代码分享列表"""
    try:
        db = current_app.db
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        shares = db.read_table('code_shares')
        shares = sorted(shares, key=lambda x: x.get('created_at', ''), reverse=True)
        shares = shares[offset:offset+limit]
        
        result = []
        for s in shares:
            user_info = get_user_info(s.get('user_id'))
            result.append({
                'id': s.get('id'),
                'title': s.get('title'),
                'description': s.get('description', ''),
                'code': s.get('code', ''),
                'language': s.get('language', 'cpp'),
                'view_count': s.get('view_count', 0),
                'like_count': s.get('like_count', 0),
                'created_at': s.get('created_at'),
                'user': user_info
            })
        
        return jsonify({'success': True, 'shares': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/code-shares', methods=['POST'])
@login_required
def create_code_share():
    """创建代码分享"""
    try:
        db = current_app.db
        
        title = request.form.get('title') or (request.get_json(silent=True) or {}).get('title')
        code = request.form.get('code') or (request.get_json(silent=True) or {}).get('code')
        description = request.form.get('description') or (request.get_json(silent=True) or {}).get('description', '')
        
        if not title or not code:
            return jsonify({'success': False, 'error': '标题和代码不能为空'}), 400
        
        data = {
            'user_id': current_user.id,
            'title': title,
            'code': code,
            'description': description,
            'language': 'cpp',
            'view_count': 0,
            'like_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        share_id = db.insert('code_shares', data)
        
        return jsonify({
            'success': True,
            'message': '分享成功',
            'share_id': share_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 教师功能 ====================

@community_bp.route('/teacher/discussions', methods=['GET'])
@login_required
def teacher_discussions():
    """教师查看所有讨论"""
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        discussions = db.find_all('discussions')
        discussions = sorted(discussions, key=lambda x: x.get('created_at', ''), reverse=True)
        
        result = []
        for d in discussions:
            user_info = get_user_info(d.get('user_id'))
            replies_count = len(db.find_by_field('replies', 'discussion_id', d.get('id')))
            
            images = []
            if d.get('images'):
                try:
                    images = json.loads(d.get('images'))
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    import logging
                    logging.warning(f"Failed to parse images JSON: {e}")
                    images = []
            
            result.append({
                'id': d.get('id'),
                'title': d.get('title'),
                'content': d.get('content', '')[:200],
                'content_full': d.get('content', ''),
                'images': images,
                'category': d.get('category', 'general'),
                'view_count': d.get('view_count', 0),
                'like_count': d.get('like_count', 0),
                'reply_count': replies_count,
                'is_sticky': d.get('is_sticky', False),
                'created_at': d.get('created_at'),
                'user': user_info
            })
        
        return jsonify({'success': True, 'discussions': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/teacher/discussions/<int:discussion_id>', methods=['PUT'])
@login_required
def teacher_update_discussion(discussion_id):
    """教师更新讨论"""
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        data = request.get_json(silent=True) or request.form
        
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'content' in data:
            update_data['content'] = data['content']
        if 'category' in data:
            update_data['category'] = data['category']
        if 'is_sticky' in data:
            update_data['is_sticky'] = data['is_sticky']
        
        if update_data:
            update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update('discussions', discussion_id, update_data)
        
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/teacher/discussions/<int:discussion_id>', methods=['DELETE'])
@login_required
def teacher_delete_discussion(discussion_id):
    """教师删除讨论"""
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        
        # 删除相关回复
        replies = db.find_by_field('replies', 'discussion_id', discussion_id)
        for reply in replies:
            db.delete('replies', reply.get('id'))
        
        # 删除相关点赞
        likes = db.find_by_field('discussion_likes', 'discussion_id', discussion_id)
        for like in likes:
            db.delete('discussion_likes', like.get('id'))
        
        # 删除讨论
        db.delete('discussions', discussion_id)
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/teacher/announcements', methods=['POST'])
@login_required
def create_announcement():
    """教师发布公告"""
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title:
            return jsonify({'success': False, 'error': '标题不能为空'}), 400
        
        # 处理图片上传
        images = []
        if 'images' in request.files:
            uploaded_files = request.files.getlist('images')
            for file in uploaded_files:
                if file and file.filename:
                    image_path = save_uploaded_image(file, 'community')
                    if image_path:
                        images.append(image_path)
        
        # 保存到数据库
        data = {
            'user_id': current_user.id,
            'title': title,
            'content': content,
            'images': json.dumps(images) if images else '',
            'category': 'announcement',
            'is_sticky': True,
            'view_count': 0,
            'like_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        discussion_id = db.insert('discussions', data)
        
        return jsonify({
            'success': True,
            'message': '公告发布成功',
            'discussion_id': discussion_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 管理员功能 ====================

@community_bp.route('/admin/users', methods=['GET'])
@login_required
def admin_users():
    """管理员查看用户列表"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        users = db.find_all('users')
        
        result = []
        for user in users:
            result.append({
                'id': user.get('id'),
                'username': user.get('username'),
                'email': user.get('email'),
                'role': user.get('role'),
                'nickname': user.get('nickname') or user.get('username'),
                'avatar': user.get('avatar'),
                'created_at': user.get('created_at')
            })
        
        return jsonify({'success': True, 'users': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@login_required
def admin_update_user(user_id):
    """管理员更新用户信息"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        data = request.get_json(silent=True) or request.form
        
        update_data = {}
        if 'role' in data:
            update_data['role'] = data['role']
        if 'nickname' in data:
            update_data['nickname'] = data['nickname']
        
        if update_data:
            update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update('users', user_id, update_data)
        
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def admin_delete_user(user_id):
    """管理员删除用户"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        
        # 删除用户相关数据
        # 删除讨论
        discussions = db.find_by_field('discussions', 'user_id', user_id)
        for discussion in discussions:
            # 删除相关回复
            replies = db.find_by_field('replies', 'discussion_id', discussion.get('id'))
            for reply in replies:
                db.delete('replies', reply.get('id'))
            # 删除相关点赞
            likes = db.find_by_field('discussion_likes', 'discussion_id', discussion.get('id'))
            for like in likes:
                db.delete('discussion_likes', like.get('id'))
            # 删除讨论
            db.delete('discussions', discussion.get('id'))
        
        # 删除回复
        replies = db.find_by_field('replies', 'user_id', user_id)
        for reply in replies:
            reply_likes = db.find_by_field('reply_likes', 'reply_id', reply.get('id'))
            for like in reply_likes:
                db.delete('reply_likes', like.get('id'))
            db.delete('replies', reply.get('id'))

        # 删除用户的点赞记录
        discussion_likes = db.find_by_field('discussion_likes', 'user_id', user_id)
        for like in discussion_likes:
            db.delete('discussion_likes', like.get('id'))

        reply_likes = db.find_by_field('reply_likes', 'user_id', user_id)
        for like in reply_likes:
            db.delete('reply_likes', like.get('id'))

        # 删除代码分享
        code_shares = db.find_by_field('code_shares', 'user_id', user_id)
        for share in code_shares:
            db.delete('code_shares', share.get('id'))

        # 删除用户
        db.delete('users', user_id)
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """管理员控制面板"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    
    try:
        db = current_app.db
        
        # 获取统计数据
        discussions = db.find_all('discussions')
        users = db.find_all('users')
        code_shares = db.find_all('code_shares')
        
        # 最近7天的活动
        recent_discussions = [d for d in discussions if d.get('created_at')]
        recent_discussions = sorted(recent_discussions, key=lambda x: x.get('created_at'), reverse=True)[:10]
        
        stats = {
            'total_discussions': len(discussions),
            'total_users': len(users),
            'total_code_shares': len(code_shares),
            'recent_discussions': recent_discussions[:5],
            'user_roles': {
                'student': len([u for u in users if u.get('role') == 'student']),
                'teacher': len([u for u in users if u.get('role') == 'teacher']),
                'admin': len([u for u in users if u.get('role') == 'admin'])
            }
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 页面路由 ====================

@community_bp.route('/')
@login_required
def community_page():
    """社区首页"""
    hour = datetime.now().hour
    if hour < 12:
        greeting = "早上好"
    elif hour < 18:
        greeting = "下午好"
    else:
        greeting = "晚上好"
    
    week_day = "周" + "日一二三四五六"[datetime.now().weekday()]
    
    return render_template('community.html',
                          greeting=greeting,
                          week_day=week_day,
                          consecutive_days=get_consecutive_learning_days(current_user),
                          user_role=current_user.role)


@community_bp.route('/post/<int:discussion_id>')
@login_required
def post_detail_page(discussion_id):
    """帖子详情页"""
    hour = datetime.now().hour
    if hour < 12:
        greeting = "早上好"
    elif hour < 18:
        greeting = "下午好"
    else:
        greeting = "晚上好"
    
    week_day = "周" + "日一二三四五六"[datetime.now().weekday()]
    
    return render_template('post_detail.html',
                          discussion_id=discussion_id,
                          greeting=greeting,
                          week_day=week_day,
                          consecutive_days=get_consecutive_learning_days(current_user),
                          user_role=current_user.role)


@community_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取社区统计数据"""
    try:
        db = current_app.db
        
        # 获取讨论数
        discussions = db.find_all('discussions')
        total_discussions = len(discussions)
        
        # 获取代码分享数
        code_shares = db.find_all('code_shares')
        total_code_shares = len(code_shares)
        
        # 获取用户数
        users = db.find_all('users')
        total_users = len(users)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_discussions': total_discussions,
                'total_code_shares': total_code_shares,
                'total_users': total_users
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 个人中心筛选功能 ====================

@community_bp.route('/my/discussions', methods=['GET'])
@login_required
def get_my_discussions():
    """获取我发布的帖子"""
    try:
        db = current_app.db
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 获取当前用户的所有讨论
        all_discussions = db.find_all('discussions')
        my_discussions = [d for d in all_discussions if d.get('user_id') == current_user.id]
        
        # 按时间排序
        my_discussions = sorted(my_discussions, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 分页
        my_discussions = my_discussions[offset:offset+limit]
        
        result = []
        for d in my_discussions:
            user_info = get_user_info(d.get('user_id'))
            replies_count = len(db.find_by_field('replies', 'discussion_id', d.get('id')))
            
            # 解析图片
            images = []
            if d.get('images'):
                try:
                    images = json.loads(d.get('images'))
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    import logging
                    logging.warning(f"Failed to parse images JSON: {e}")
                    images = []
            
            result.append({
                'id': d.get('id'),
                'title': d.get('title'),
                'content': d.get('content', '')[:200],
                'images': images,
                'view_count': d.get('view_count', 0),
                'like_count': d.get('like_count', 0),
                'reply_count': replies_count,
                'created_at': d.get('created_at'),
                'user': user_info
            })
        
        return jsonify({'success': True, 'discussions': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/my/replies', methods=['GET'])
@login_required
def get_my_replies():
    """获取我回复的帖子"""
    try:
        db = current_app.db
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 获取当前用户的所有回复
        all_replies = db.find_all('replies')
        my_replies = [r for r in all_replies if r.get('user_id') == current_user.id]
        
        # 获取这些回复对应的帖子ID（去重）
        discussion_ids = list(set([r.get('discussion_id') for r in my_replies]))
        
        # 获取帖子详情
        result = []
        for discussion_id in discussion_ids:
            d = db.find_by_id('discussions', discussion_id)
            if d:
                user_info = get_user_info(d.get('user_id'))
                replies_count = len(db.find_by_field('replies', 'discussion_id', discussion_id))
                
                # 解析图片
                images = []
                if d.get('images'):
                    try:
                        images = json.loads(d.get('images'))
                    except (json.JSONDecodeError, TypeError, ValueError) as e:
                        import logging
                        logging.warning(f"Failed to parse images JSON: {e}")
                        images = []
                
                result.append({
                    'id': d.get('id'),
                    'title': d.get('title'),
                    'content': d.get('content', '')[:200],
                    'images': images,
                    'view_count': d.get('view_count', 0),
                    'like_count': d.get('like_count', 0),
                    'reply_count': replies_count,
                    'created_at': d.get('created_at'),
                    'user': user_info
                })
        
        # 按时间排序
        result = sorted(result, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 分页
        result = result[offset:offset+limit]
        
        return jsonify({'success': True, 'discussions': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/replies/to-me', methods=['GET'])
@login_required
def get_replies_to_me():
    """获取回复我的评论"""
    try:
        db = current_app.db
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 获取我发布的所有帖子
        all_discussions = db.find_all('discussions')
        my_discussion_ids = [d.get('id') for d in all_discussions if d.get('user_id') == current_user.id]
        
        # 获取这些帖子的所有回复
        all_replies = db.find_all('replies')
        replies_to_me = [r for r in all_replies if r.get('discussion_id') in my_discussion_ids and r.get('user_id') != current_user.id]
        
        # 按时间排序
        replies_to_me = sorted(replies_to_me, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 分页
        replies_to_me = replies_to_me[offset:offset+limit]
        
        result = []
        for r in replies_to_me:
            user_info = get_user_info(r.get('user_id'))
            discussion = db.find_by_id('discussions', r.get('discussion_id'))
            
            result.append({
                'id': r.get('id'),
                'content': r.get('content'),
                'like_count': r.get('like_count', 0),
                'created_at': r.get('created_at'),
                'user': user_info,
                'discussion': {
                    'id': discussion.get('id') if discussion else None,
                    'title': discussion.get('title') if discussion else '未知帖子'
                }
            })
        
        return jsonify({'success': True, 'replies': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
