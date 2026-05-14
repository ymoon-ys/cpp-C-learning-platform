// 任务勾选功能
const checkboxes = document.querySelectorAll('.task-item input[type="checkbox"]');

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        const label = this.nextElementSibling;
        if (this.checked) {
            label.style.textDecoration = 'line-through';
            label.style.color = '#95a5a6';
        } else {
            label.style.textDecoration = 'none';
            label.style.color = '#34495e';
        }
    });
});

// 侧边栏导航切换
const navItems = document.querySelectorAll('.sidebar-nav li');

navItems.forEach(item => {
    item.addEventListener('click', function() {
        navItems.forEach(navItem => navItem.classList.remove('active'));
        this.classList.add('active');
    });
});

// 课程卡片悬停效果
const courseCards = document.querySelectorAll('.course-card');

courseCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
        this.style.boxShadow = '0 5px 20px rgba(0,0,0,0.15)';
    });

    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    });
});

// 继续学习按钮点击效果
const continueBtns = document.querySelectorAll('.continue-btn');

continueBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        alert('跳转到课程详情页');
    });
});

// 聊天窗口点击效果
const chatWindow = document.querySelector('.chat-window');

if (chatWindow) {
    chatWindow.addEventListener('click', function() {
        alert('打开AI助手聊天窗口');
    });
}

// 查看全部链接点击效果
const moreLinks = document.querySelectorAll('.more');

moreLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        alert('跳转到更多页面');
    });
});

// 模拟时间更新
function updateTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    const timeString = `${hours}:${minutes}:${seconds}`;
    console.log('当前时间:', timeString);
}

setInterval(updateTime, 1000);

// 登录功能 - Flask应用使用服务器端Session认证，无需前端处理
// 安全提示：密码永远不应在客户端存储

// 检查登录状态 - Flask应用使用服务器端Session管理登录状态，无需localStorage检查
function checkLoginStatus() {
    // Flask应用使用服务器端Session管理登录状态，无需localStorage检查
}

// 设置页面 - 账户安全表单
// 密码修改由Flask服务器端处理，无需在前端存储密码

// 设置页面 - 基本资料表单
const profileForm = document.getElementById('profileForm');

if (profileForm) {
    // 表单会正常提交到服务器，不需要阻止
}

// 头像预览功能
const avatarInput = document.getElementById('avatar');

if (avatarInput) {
    avatarInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const currentAvatar = document.querySelector('.current-avatar img');
                if (currentAvatar) {
                    currentAvatar.src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        }
    });
}

// 点击更换头像标签时触发文件选择
const avatarLabel = document.querySelector('label[for="avatar"]');
if (avatarLabel) {
    avatarLabel.addEventListener('click', function() {
        document.getElementById('avatar').click();
    });
}

// 退出登录功能 - 由Flask服务器端处理
const logoutBtn = document.getElementById('logoutBtn');

if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
        if (confirm('确定要退出登录吗？')) {
            // 由Flask后端处理退出登录
            window.location.href = '/auth/logout';
        }
    });
}

// 注销账户功能
const deleteAccountBtn = document.getElementById('deleteAccountBtn');
const deleteModal = document.getElementById('deleteModal');
const cancelDelete = document.getElementById('cancelDelete');
const confirmDelete = document.getElementById('confirmDelete');

if (deleteAccountBtn) {
    deleteAccountBtn.addEventListener('click', function() {
        if (deleteModal) {
            deleteModal.classList.add('show');
        }
    });
}

if (cancelDelete) {
    cancelDelete.addEventListener('click', function() {
        if (deleteModal) {
            deleteModal.classList.remove('show');
        }
    });
}

if (confirmDelete) {
    confirmDelete.addEventListener('click', function() {
        // 由Flask后端处理账户注销
        window.location.href = '/auth/delete-account';
    });
}

// 点击模态框外部关闭
if (deleteModal) {
    deleteModal.addEventListener('click', function(e) {
        if (e.target === deleteModal) {
            deleteModal.classList.remove('show');
        }
    });
}

// 用户头像点击 - 跳转到设置页面
const userIcon = document.querySelector('.user-icon');

if (userIcon) {
    userIcon.addEventListener('click', function() {
        window.location.href = '/settings';
    });
    userIcon.style.cursor = 'pointer';
}

// 页面加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');
    updateTime();
    checkLoginStatus();
    
    // 初始化设置页面
    initSettingsPage();
    
    // 课程页面交互功能
    initCoursePage();
    
    // 课程详情页面交互功能
    initCourseDetailPage();
    
    // 栏目详情页面交互功能
    initLessonDetailPage();
});

// 课程页面初始化
function initCoursePage() {
    const courseCards = document.querySelectorAll('.course-card');
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    // 课程卡片点击事件
    if (courseCards.length > 0) {
        courseCards.forEach(card => {
            card.addEventListener('click', function() {
                const courseId = this.dataset.course;
                window.location.href = 'course-detail.html';
            });
        });
    }
    
    // 筛选按钮点击事件
    if (filterBtns.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                filterBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const filter = this.textContent.trim();
                console.log('筛选:', filter);
                // 这里可以添加筛选逻辑
            });
        });
    }
}

// 课程详情页面初始化
function initCourseDetailPage() {
    const navBtns = document.querySelectorAll('.nav-btn');
    const chapterHeaders = document.querySelectorAll('.chapter-header');
    const lessonBtns = document.querySelectorAll('.lesson-btn');
    
    // 导航按钮点击事件
    if (navBtns.length > 0) {
        navBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                navBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
    
    // 章节标题点击事件（展开/折叠）
    if (chapterHeaders.length > 0) {
        chapterHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                if (content) {
                    content.style.display = content.style.display === 'none' ? 'block' : 'block';
                }
            });
        });
    }
    
    // 课时按钮点击事件
    if (lessonBtns.length > 0) {
        lessonBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                window.location.href = 'lesson-detail.html';
            });
        });
    }
}

// 栏目详情页面初始化
function initLessonDetailPage() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const playButton = document.querySelector('.play-button');
    
    // 标签页切换事件
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tabId = this.dataset.tab;
                
                // 更新标签按钮状态
                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // 更新标签内容
                tabPanes.forEach(pane => {
                    pane.classList.remove('active');
                });
                
                const targetPane = document.getElementById(tabId);
                if (targetPane) {
                    targetPane.classList.add('active');
                }
            });
        });
    }
    
    // 视频播放按钮点击事件
    if (playButton) {
        playButton.addEventListener('click', function() {
            alert('视频开始播放');
        });
    }
}

// 控制按钮点击事件
const controlBtns = document.querySelectorAll('.control-btn');
if (controlBtns.length > 0) {
    controlBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.textContent.trim();
            if (action === '上一课') {
                alert('跳转到上一课');
            } else if (action === '下一课') {
                alert('跳转到下一课');
            } else if (action === '下载视频') {
                alert('开始下载视频');
            }
        });
    });
}

// 练习按钮点击事件
const exerciseBtns = document.querySelectorAll('.exercise-btn');
if (exerciseBtns.length > 0) {
    exerciseBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            alert('开始练习');
        });
    });
}

// 操作按钮点击事件
const actionBtns = document.querySelectorAll('.action-btn');
if (actionBtns.length > 0) {
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.textContent.trim();
            if (action === '做笔记') {
                alert('打开笔记编辑器');
            } else if (action === '下载文档') {
                alert('开始下载文档');
            }
        });
    });
}

// 讨论页面初始化
function initDiscussionPage() {
    // 标签页切换
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tabId = this.dataset.tab;
                
                // 更新标签按钮状态
                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // 更新标签内容
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                
                const targetContent = document.getElementById(tabId);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }
    
    // 创建小组按钮点击事件
    const createGroupBtn = document.querySelector('.create-group-btn');
    const createGroupModal = document.getElementById('create-group-modal');
    const closeModalBtns = document.querySelectorAll('.close-modal');
    const submitCreateGroup = document.querySelector('.submit-create-group');
    
    if (createGroupBtn) {
        createGroupBtn.addEventListener('click', function() {
            if (createGroupModal) {
                createGroupModal.classList.add('show');
            }
        });
    }
    
    // 关闭模态框
    if (closeModalBtns.length > 0) {
        closeModalBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.classList.remove('show');
                }
            });
        });
    }
    
    // 点击模态框外部关闭
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });
    
    // 提交创建小组
    if (submitCreateGroup) {
        submitCreateGroup.addEventListener('click', function() {
            const groupName = document.getElementById('group-name').value;
            const groupDescription = document.getElementById('group-description').value;
            
            if (!groupName) {
                alert('请输入小组名称');
                return;
            }
            
            // 生成6位随机编码
            const groupCode = generateGroupCode();
            
            // 模拟创建小组
            alert(`小组创建成功！\n小组名称: ${groupName}\n小组编码: ${groupCode}`);
            
            // 关闭模态框
            if (createGroupModal) {
                createGroupModal.classList.remove('show');
            }
            
            // 清空表单
            document.getElementById('group-name').value = '';
            document.getElementById('group-description').value = '';
        });
    }
    
    // 加入小组按钮点击事件
    const joinGroupBtn = document.querySelector('.join-group-btn');
    const groupCodeInput = document.getElementById('group-code');
    
    if (joinGroupBtn) {
        joinGroupBtn.addEventListener('click', function() {
            const code = groupCodeInput.value.trim();
            
            if (!code) {
                alert('请输入小组编码');
                return;
            }
            
            if (code.length !== 6) {
                alert('小组编码必须是6位数字');
                return;
            }
            
            // 模拟加入小组
            alert(`加入小组成功！\n小组编码: ${code}`);
            
            // 清空输入
            groupCodeInput.value = '';
        });
    }
    
    // 进入小组按钮点击事件
    const enterGroupBtns = document.querySelectorAll('.enter-group-btn');
    const groupModal = document.getElementById('group-modal');
    
    if (enterGroupBtns.length > 0) {
        enterGroupBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const groupCard = this.closest('.group-card');
                const groupName = groupCard.querySelector('h4').textContent;
                const groupCode = groupCard.querySelector('.group-code').textContent.replace('编码: ', '');
                
                // 更新模态框内容
                if (groupModal) {
                    document.getElementById('modal-title').textContent = groupName;
                    document.getElementById('modal-group-name').textContent = groupName;
                    document.getElementById('modal-group-code').textContent = groupCode;
                    groupModal.classList.add('show');
                }
            });
        });
    }
    
    // 小组内发布帖子
    const groupPostBtn = document.querySelector('.post-btn');
    const groupPostContent = document.getElementById('group-post-content');
    const groupPostsList = document.getElementById('group-posts-list');
    
    if (groupPostBtn) {
        groupPostBtn.addEventListener('click', function() {
            const content = groupPostContent.value.trim();
            
            if (!content) {
                alert('请输入帖子内容');
                return;
            }
            
            // 创建新帖子
            const post = createPost(content);
            
            // 添加到帖子列表
            if (groupPostsList) {
                groupPostsList.insertBefore(post, groupPostsList.firstChild);
            }
            
            // 清空输入
            groupPostContent.value = '';
        });
    }
    
    // 公共论坛发布帖子
    const forumPostContent = document.getElementById('forum-post-content');
    const forumPostsList = document.getElementById('forum-posts-list');
    
    if (groupPostBtn) {
        groupPostBtn.addEventListener('click', function() {
            const content = forumPostContent ? forumPostContent.value.trim() : '';
            
            if (!content) {
                return;
            }
            
            // 创建新帖子
            const post = createPost(content);
            
            // 添加到帖子列表
            if (forumPostsList) {
                forumPostsList.insertBefore(post, forumPostsList.firstChild);
            }
            
            // 清空输入
            if (forumPostContent) {
                forumPostContent.value = '';
            }
        });
    }
    
    // 回复按钮点击事件
    const replyBtns = document.querySelectorAll('.reply-btn');
    replyBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const post = this.closest('.post');
            const replies = post.querySelector('.replies');
            const replyForm = replies.querySelector('.reply-form');
            
            if (replyForm) {
                replyForm.style.display = replyForm.style.display === 'none' ? 'flex' : 'flex';
            }
        });
    });
    
    // 回复提交
    const replySubmitBtns = document.querySelectorAll('.reply-submit');
    replySubmitBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const replyForm = this.closest('.reply-form');
            const replyInput = replyForm.querySelector('.reply-input');
            const content = replyInput.value.trim();
            
            if (!content) {
                alert('请输入回复内容');
                return;
            }
            
            // 创建新回复
            const reply = createReply(content);
            
            // 添加到回复列表
            const replies = replyForm.closest('.replies');
            replies.insertBefore(reply, replyForm);
            
            // 清空输入
            replyInput.value = '';
        });
    });
    
    // 删除帖子按钮点击事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-post-btn')) {
            if (confirm('确定要删除这个帖子吗？')) {
                const post = e.target.closest('.post');
                if (post) {
                    post.remove();
                }
            }
        }
    });
    
    // 初始化CodeMirror编辑器（如果存在）
    if (typeof CodeMirror !== 'undefined') {
        console.log('CodeMirror编辑器初始化成功');
    }
}

// 生成6位随机小组编码
function generateGroupCode() {
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += Math.floor(Math.random() * 10);
    }
    return code;
}

// 创建帖子元素
function createPost(content) {
    const post = document.createElement('div');
    post.className = 'post';
    
    const now = new Date();
    const timeString = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
    
    post.innerHTML = `
        <div class="post-header">
            <span class="post-author">当前用户</span>
            <span class="post-time">${timeString}</span>
            <button class="delete-post-btn">删除</button>
        </div>
        <div class="post-content">
            <p>${content}</p>
        </div>
        <div class="post-actions">
            <button class="reply-btn">回复 (0)</button>
        </div>
        <div class="replies">
            <div class="reply-form">
                <textarea placeholder="回复..." class="reply-input"></textarea>
                <button class="reply-submit">回复</button>
            </div>
        </div>
    `;
    
    return post;
}

// 创建回复元素
function createReply(content) {
    const reply = document.createElement('div');
    reply.className = 'reply';
    
    const now = new Date();
    const timeString = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
    
    reply.innerHTML = `
        <div class="reply-header">
            <span class="reply-author">当前用户</span>
            <span class="reply-time">${timeString}</span>
        </div>
        <div class="reply-content">
            <p>${content}</p>
        </div>
    `;
    
    return reply;
}

// 初始化设置页面
function initSettingsPage() {
    const accountInput = document.getElementById('account');
    const nicknameInput = document.getElementById('nickname');
    const currentAvatar = document.querySelector('.current-avatar');
    const avatarInput = document.getElementById('avatar');
    const profileForm = document.getElementById('profileForm');
    const securityForm = document.getElementById('securityForm');
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    
    // 标签页切换功能
    const tabBtns = document.querySelectorAll('.settings-tabs .tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有激活状态
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // 激活当前标签
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    if (accountInput) {
        // 不设置默认值，使用模板渲染的值
    }
    
    if (nicknameInput) {
        // 不设置默认值，使用模板渲染的值
    }
    
    if (currentAvatar) {
        // 不设置默认值，使用模板渲染的值
    }
    
    // 头像上传功能
    if (avatarInput && currentAvatar) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    currentAvatar.src = e.target.result;
                    
                    // 实时更新右上角的头像
                    const headerAvatar = document.querySelector('.header-right .user-icon img');
                    if (headerAvatar) {
                        headerAvatar.src = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // 昵称输入实时更新
    if (nicknameInput) {
        nicknameInput.addEventListener('input', function() {
            const nickname = this.value.trim();
            if (nickname) {
                // 实时更新右上角的昵称
                const greetingElement = document.querySelector('.header-right .greeting p:first-child');
                if (greetingElement) {
                    // 保留问候语部分，只更新昵称
                    const text = greetingElement.textContent;
                    const greetingPart = text.split('，')[0];
                    greetingElement.textContent = `${greetingPart}，${nickname}`;
                }
            }
        });
    }
    
    // 基本资料表单提交功能 - 让表单正常提交到服务器
    if (profileForm) {
        // 不拦截表单提交，让Flask后端处理
    }
    
    // 密码修改功能
    if (securityForm) {
        securityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (!currentPassword) {
                showNotification('请输入当前密码！', 'error');
                return;
            }
            
            if (!newPassword) {
                showNotification('请输入新密码！', 'error');
                return;
            }
            
            if (newPassword.length < 6) {
                showNotification('新密码长度不能少于6位！', 'error');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                showNotification('两次输入的密码不一致！', 'error');
                return;
            }
            
            // 提交到Flask后端处理
            fetch('/settings/password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('密码修改成功！', 'success');
                    securityForm.reset();
                } else {
                    showNotification(data.message || '密码修改失败！', 'error');
                }
            })
            .catch(error => {
                showNotification('网络错误，请稍后重试！', 'error');
            });
        });
    }
    
    // 账户注销功能
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function() {
            if (confirm('确定要注销账户吗？此操作不可恢复，所有数据将被永久删除。')) {
                // 提交到Flask后端处理
                fetch('/auth/delete-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('账户已注销！', 'success');
                        setTimeout(() => {
                            window.location.href = '/login';
                        }, 1500);
                    } else {
                        showNotification(data.message || '注销失败！', 'error');
                    }
                })
                .catch(error => {
                    showNotification('网络错误，请稍后重试！', 'error');
                });
            }
        });
    }
}

// 显示通知消息
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    // 根据类型设置背景色
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#28a745';
            break;
        case 'error':
            notification.style.backgroundColor = '#dc3545';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ffc107';
            notification.style.color = '#333';
            break;
        default:
            notification.style.backgroundColor = '#17a2b8';
    }
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 设置页面功能
// 只有在设置页面才初始化
if (window.location.pathname.includes('settings')) {
    initSettingsPage();
}

// 运行代码
function runCode() {
    const codeEditor = document.getElementById('codeEditor');
    const outputPane = document.getElementById('outputPane');
    const errorList = document.getElementById('errorList');
    const knowledgeList = document.getElementById('knowledgeList');
    
    if (!codeEditor) return;
    
    const code = codeEditor.value.trim();
    
    if (!code) {
        alert('请输入或上传代码');
        return;
    }
    
    // 清空之前的结果
    if (outputPane) {
        outputPane.innerHTML = '<div class="vs-output-placeholder"><p>正在运行代码...</p></div>';
    }
    if (errorList) {
        errorList.innerHTML = '<div class="vs-errors-placeholder"><p>正在分析代码...</p></div>';
    }
    if (knowledgeList) {
        knowledgeList.innerHTML = '<div class="vs-knowledge-placeholder"><p>正在关联知识点...</p></div>';
    }
    
    // 模拟代码运行和分析
    setTimeout(() => {
        const result = analyzeCode(code);
        displayResults(result);
    }, 1000);
}

// 分析代码
function analyzeCode(code) {
    const errors = [];
    const warnings = [];
    
    // 检查语法错误
    const syntaxErrors = checkSyntaxErrors(code);
    errors.push(...syntaxErrors);
    
    // 检查常见错误
    const commonErrors = checkCommonErrors(code);
    errors.push(...commonErrors.errors);
    warnings.push(...commonErrors.warnings);
    
    // 生成运行结果
    const output = generateOutput(code, errors);
    
    return {
        output,
        errors,
        warnings
    };
}

// 检查语法错误
function checkSyntaxErrors(code) {
    const errors = [];
    const lines = code.split('\n');
    
    // 全局括号计数
    let totalOpenBraces = 0;
    let totalCloseBraces = 0;
    let totalOpenParens = 0;
    let totalCloseParens = 0;
    
    lines.forEach((line, index) => {
        const lineNum = index + 1;
        const trimmedLine = line.trim();
        
        // 跳过空行和注释
        if (!trimmedLine || trimmedLine.startsWith('//') || trimmedLine.startsWith('#')) {
            return;
        }
        
        // 检查缺少分号 - 只检查真正的语句行
        const isStatementLine = !trimmedLine.endsWith('{') && !trimmedLine.endsWith('}') && 
                              !trimmedLine.includes('for(') && !trimmedLine.includes('if(') && 
                              !trimmedLine.includes('while(') && !trimmedLine.includes('switch(') && 
                              !trimmedLine.includes('do') && !trimmedLine.includes('case') && 
                              !trimmedLine.includes('default') && !trimmedLine.includes('return') && 
                              !trimmedLine.includes('break') && !trimmedLine.includes('continue');
        
        if (isStatementLine && !trimmedLine.endsWith(';')) {
            // 进一步检查是否是函数声明或其他不需要分号的结构
            const isFunctionDeclaration = trimmedLine.includes('(') && trimmedLine.includes(')') && 
                                         (trimmedLine.includes('void') || trimmedLine.includes('int') || 
                                          trimmedLine.includes('float') || trimmedLine.includes('double') || 
                                          trimmedLine.includes('bool') || trimmedLine.includes('char'));
            
            if (!isFunctionDeclaration) {
                errors.push({
                    type: 'error',
                    location: `第${lineNum}行`,
                    message: '缺少分号',
                    suggestion: '在语句末尾添加分号 (;)'
                });
            }
        }
        
        // 累计括号计数
        totalOpenBraces += (line.match(/{/g) || []).length;
        totalCloseBraces += (line.match(/}/g) || []).length;
        totalOpenParens += (line.match(/\(/g) || []).length;
        totalCloseParens += (line.match(/\)/g) || []).length;
    });
    
    // 检查全局括号匹配
    if (totalOpenBraces > totalCloseBraces) {
        errors.push({
            type: 'error',
            location: '全局',
            message: '缺少闭合大括号',
            suggestion: '添加缺失的闭合大括号 (})'
        });
    } else if (totalOpenBraces < totalCloseBraces) {
        errors.push({
            type: 'error',
            location: '全局',
            message: '多余的闭合大括号',
            suggestion: '移除多余的闭合大括号 (})'
        });
    }
    
    if (totalOpenParens > totalCloseParens) {
        errors.push({
            type: 'error',
            location: '全局',
            message: '缺少闭合圆括号',
            suggestion: '添加缺失的闭合圆括号 ())'
        });
    } else if (totalOpenParens < totalCloseParens) {
        errors.push({
            type: 'error',
            location: '全局',
            message: '多余的闭合圆括号',
            suggestion: '移除多余的闭合圆括号 ())'
        });
    }
    
    return errors;
}

// 检查常见错误
function checkCommonErrors(code) {
    const errors = [];
    const warnings = [];
    
    // 检查未初始化的变量
    const uninitializedVars = code.match(/int\s+\w+\s*;/g) || [];
    uninitializedVars.forEach(match => {
        warnings.push({
            type: 'warning',
            location: '全局',
            message: '变量可能未初始化',
            suggestion: '建议在使用变量前进行初始化'
        });
    });
    
    // 检查内存泄漏风险
    if (code.includes('new ') && !code.includes('delete ')) {
        errors.push({
            type: 'error',
            location: '全局',
            message: '可能的内存泄漏',
            suggestion: '使用new分配的内存应该使用delete释放'
        });
    }
    
    // 检查数组越界风险
    if (code.includes('for') && code.includes('[i]')) {
        warnings.push({
            type: 'warning',
            location: '循环',
            message: '可能的数组越界',
            suggestion: '确保循环变量在数组范围内'
        });
    }
    
    // 检查指针未初始化
    if (code.includes('*') && !code.includes('= nullptr') && !code.includes('= NULL')) {
        warnings.push({
            type: 'warning',
            location: '指针',
            message: '指针可能未初始化',
            suggestion: '建议将指针初始化为nullptr'
        });
    }
    
    // 检查未使用的变量
    const varDeclarations = code.match(/int\s+(\w+)/g) || [];
    varDeclarations.forEach(decl => {
        const varName = decl.replace('int ', '');
        const usageCount = (code.match(new RegExp(varName, 'g')) || []).length;
        if (usageCount <= 1) {
            warnings.push({
                type: 'warning',
                location: '变量声明',
                message: `变量 ${varName} 可能未使用`,
                suggestion: '检查是否需要使用该变量或删除声明'
            });
        }
    });
    
    return { errors, warnings };
}

// 生成输出结果
function generateOutput(code, errors) {
    if (errors.length > 0) {
        return '编译失败！\n请查看错误信息了解详情。';
    }
    
    let output = '编译成功！\n\n';
    
    if (code.includes('cout')) {
        output += '程序输出:\n';
        const coutMatches = code.match(/cout\s*<<\s*([^;]+);/g) || [];
        coutMatches.forEach(match => {
            const content = match.replace(/cout\s*<<\s*/, '').replace(/;/, '');
            if (content.includes('"')) {
                output += content.replace(/"/g, '') + '\n';
            } else {
                output += `[变量值: ${content.trim()}]\n`;
            }
        });
    } else {
        output += '程序编译成功，但没有输出。\n';
        output += '提示: 使用cout语句来输出结果。';
    }
    
    return output;
}

// 显示结果
function displayResults(result) {
    const outputPane = document.getElementById('outputPane');
    const errorList = document.getElementById('errorList');
    const knowledgeList = document.getElementById('knowledgeList');
    
    // 显示运行结果
    if (outputPane) {
        outputPane.innerHTML = `<div class="output-content-text">${escapeHtml(result.output)}</div>`;
    }
    
    // 显示错误信息
    const allErrors = [...result.errors, ...result.warnings];
    if (allErrors.length > 0) {
        if (errorList) {
            errorList.innerHTML = '';
            allErrors.forEach(error => {
                const errorItem = document.createElement('div');
                errorItem.className = `error-item ${error.type}`;
                errorItem.innerHTML = `
                    <div class="error-header">
                        <span class="error-type">${error.type === 'error' ? '错误' : '警告'}</span>
                        <span class="error-location">${escapeHtml(error.location)}</span>
                    </div>
                    <p class="error-message">${escapeHtml(error.message)}</p>
                    <p class="error-suggestion">💡 建议: ${escapeHtml(error.suggestion)}</p>
                `;
                errorList.appendChild(errorItem);
            });
        }
    } else {
        if (errorList) {
            errorList.innerHTML = '<div class="vs-errors-placeholder"><p>✓ 代码没有发现错误</p></div>';
        }
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 搜索功能
const searchBtn = document.getElementById('searchBtn');
if (searchBtn) {
    searchBtn.addEventListener('click', function() {
        const searchInput = document.getElementById('searchInput');
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
            window.location.href = `?search=${encodeURIComponent(searchTerm)}`;
        } else {
            window.location.href = window.location.pathname;
        }
    });

    // 回车键搜索
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }
}

// 初始化讨论页面功能
if (window.location.pathname.includes('community')) {
    initDiscussionPage();
}
