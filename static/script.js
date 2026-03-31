﻿﻿﻿// 浠诲姟鍕鹃€夊姛鑳?const checkboxes = document.querySelectorAll('.task-item input[type="checkbox"]');

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

// 渚ц竟鏍忓鑸垏鎹?const navItems = document.querySelectorAll('.sidebar-nav li');

navItems.forEach(item => {
    item.addEventListener('click', function() {
        navItems.forEach(navItem => navItem.classList.remove('active'));
        this.classList.add('active');
    });
});

// 璇剧▼鍗＄墖鎮仠鏁堟灉
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

// 缁х画瀛︿範鎸夐挳鐐瑰嚮鏁堟灉
const continueBtns = document.querySelectorAll('.continue-btn');

continueBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        alert('璺宠浆鍒拌绋嬭鎯呴〉');
    });
});

// 鑱婂ぉ绐楀彛鐐瑰嚮鏁堟灉
const chatWindow = document.querySelector('.chat-window');

if (chatWindow) {
    chatWindow.addEventListener('click', function() {
        alert('鎵撳紑AI鍔╂墜鑱婂ぉ绐楀彛');
    });
}

// 鏌ョ湅鍏ㄩ儴閾炬帴鐐瑰嚮鏁堟灉
const moreLinks = document.querySelectorAll('.more');

moreLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        alert('璺宠浆鍒版洿澶氶〉闈?);
    });
});

// 妯℃嫙鏃堕棿鏇存柊
function updateTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    const timeString = `${hours}:${minutes}:${seconds}`;
    console.log('褰撳墠鏃堕棿:', timeString);
}

setInterval(updateTime, 1000);

// 鐧诲綍鍔熻兘 - 浠呭湪闈濬lask鐜涓嬩娇鐢?const loginForm = document.getElementById('loginForm');

if (loginForm && window.location.href.includes('file://')) {
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            alert('璇疯緭鍏ョ敤鎴峰悕鍜屽瘑鐮?);
            return;
        }
        
        // 浠巐ocalStorage璇诲彇淇濆瓨鐨勫瘑鐮?        const savedPassword = localStorage.getItem('password') || '123456';
        const savedUsername = localStorage.getItem('username') || '0631250124';
        
        // 鐧诲綍楠岃瘉
        if (username === savedUsername && password === savedPassword) {
            // 淇濆瓨鐧诲綍鐘舵€?            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('username', username);
            
            alert('鐧诲綍鎴愬姛锛?);
            window.location.href = 'index.html';
        } else {
            alert('鐢ㄦ埛鍚嶆垨瀵嗙爜閿欒锛?);
        }
    });
}

// 妫€鏌ョ櫥褰曠姸鎬?function checkLoginStatus() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const currentPage = window.location.pathname.split('/').pop();
    
    if (!isLoggedIn && currentPage === 'index.html') {
        // 濡傛灉鏈櫥褰曚笖鍦ㄤ富椤碉紝鍙互閫夋嫨閲嶅畾鍚戝埌鐧诲綍椤?        // window.location.href = 'login.html';
    }
}

// 璁剧疆椤甸潰 - 璐︽埛瀹夊叏琛ㄥ崟
const securityForm = document.getElementById('securityForm');

if (securityForm) {
    securityForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const account = document.getElementById('account').value;
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        const savedPassword = localStorage.getItem('password') || '123456';
        
        if (!currentPassword) {
            alert('璇疯緭鍏ュ綋鍓嶅瘑鐮?);
            return;
        }
        
        if (currentPassword !== savedPassword) {
            alert('褰撳墠瀵嗙爜閿欒');
            return;
        }
        
        if (newPassword && newPassword !== confirmPassword) {
            alert('涓ゆ杈撳叆鐨勬柊瀵嗙爜涓嶄竴鑷?);
            return;
        }
        
        if (newPassword) {
            localStorage.setItem('password', newPassword);
        }
        
        localStorage.setItem('username', account);
        localStorage.setItem('nickname', account);
        
        alert('璐︽埛瀹夊叏淇℃伅宸叉洿鏂帮紒');
        
        updateUserInfo();
    });
}

// 璁剧疆椤甸潰 - 鍩烘湰璧勬枡琛ㄥ崟
const profileForm = document.getElementById('profileForm');

if (profileForm) {
    // 琛ㄥ崟浼氭甯告彁浜ゅ埌鏈嶅姟鍣紝涓嶉渶瑕侀樆姝?}

// 澶村儚棰勮鍔熻兘
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

// 鐐瑰嚮鏇存崲澶村儚鏍囩鏃惰Е鍙戞枃浠堕€夋嫨
const avatarLabel = document.querySelector('label[for="avatar"]');
if (avatarLabel) {
    avatarLabel.addEventListener('click', function() {
        document.getElementById('avatar').click();
    });
}

// 閫€鍑虹櫥褰曞姛鑳?const logoutBtn = document.getElementById('logoutBtn');

if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
        if (confirm('纭畾瑕侀€€鍑虹櫥褰曞悧锛?)) {
            localStorage.removeItem('isLoggedIn');
            alert('宸查€€鍑虹櫥褰?);
            window.location.href = 'login.html';
        }
    });
}

// 娉ㄩ攢璐︽埛鍔熻兘
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
        // 娓呴櫎鎵€鏈夌敤鎴锋暟鎹?        localStorage.clear();
        alert('璐︽埛宸叉敞閿€锛屽嵆灏嗚繑鍥炵櫥褰曢〉闈?);
        window.location.href = 'login.html';
    });
}

// 鐐瑰嚮妯℃€佹澶栭儴鍏抽棴
if (deleteModal) {
    deleteModal.addEventListener('click', function(e) {
        if (e.target === deleteModal) {
            deleteModal.classList.remove('show');
        }
    });
}

// 鐢ㄦ埛澶村儚鐐瑰嚮 - 璺宠浆鍒拌缃〉闈?const userIcon = document.querySelector('.user-icon');

if (userIcon) {
    userIcon.addEventListener('click', function() {
        window.location.href = 'settings.html';
    });
    userIcon.style.cursor = 'pointer';
}

// 椤甸潰鍔犺浇瀹屾垚鍚庢墽琛?window.addEventListener('DOMContentLoaded', function() {
    console.log('椤甸潰鍔犺浇瀹屾垚');
    updateTime();
    checkLoginStatus();
    
    // 鍒濆鍖栬缃〉闈?    initSettingsPage();
    
    // 璇剧▼椤甸潰浜や簰鍔熻兘
    initCoursePage();
    
    // 璇剧▼璇︽儏椤甸潰浜や簰鍔熻兘
    initCourseDetailPage();
    
    // 鏍忕洰璇︽儏椤甸潰浜や簰鍔熻兘
    initLessonDetailPage();
});

// 璇剧▼椤甸潰鍒濆鍖?function initCoursePage() {
    const courseCards = document.querySelectorAll('.course-card');
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    // 璇剧▼鍗＄墖鐐瑰嚮浜嬩欢
    if (courseCards.length > 0) {
        courseCards.forEach(card => {
            card.addEventListener('click', function() {
                const courseId = this.dataset.course;
                window.location.href = 'course-detail.html';
            });
        });
    }
    
    // 绛涢€夋寜閽偣鍑讳簨浠?    if (filterBtns.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                filterBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const filter = this.textContent.trim();
                console.log('绛涢€?', filter);
                // 杩欓噷鍙互娣诲姞绛涢€夐€昏緫
            });
        });
    }
}

// 璇剧▼璇︽儏椤甸潰鍒濆鍖?function initCourseDetailPage() {
    const navBtns = document.querySelectorAll('.nav-btn');
    const chapterHeaders = document.querySelectorAll('.chapter-header');
    const lessonBtns = document.querySelectorAll('.lesson-btn');
    
    // 瀵艰埅鎸夐挳鐐瑰嚮浜嬩欢
    if (navBtns.length > 0) {
        navBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                navBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
    
    // 绔犺妭鏍囬鐐瑰嚮浜嬩欢锛堝睍寮€/鎶樺彔锛?    if (chapterHeaders.length > 0) {
        chapterHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                if (content) {
                    content.style.display = content.style.display === 'none' ? 'block' : 'block';
                }
            });
        });
    }
    
    // 璇炬椂鎸夐挳鐐瑰嚮浜嬩欢
    if (lessonBtns.length > 0) {
        lessonBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                window.location.href = 'lesson-detail.html';
            });
        });
    }
}

// 鏍忕洰璇︽儏椤甸潰鍒濆鍖?function initLessonDetailPage() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const playButton = document.querySelector('.play-button');
    
    // 鏍囩椤靛垏鎹簨浠?    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tabId = this.dataset.tab;
                
                // 鏇存柊鏍囩鎸夐挳鐘舵€?                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // 鏇存柊鏍囩鍐呭
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
    
    // 瑙嗛鎾斁鎸夐挳鐐瑰嚮浜嬩欢
    if (playButton) {
        playButton.addEventListener('click', function() {
            alert('瑙嗛寮€濮嬫挱鏀?);
        });
    }
}

// 鎺у埗鎸夐挳鐐瑰嚮浜嬩欢
const controlBtns = document.querySelectorAll('.control-btn');
if (controlBtns.length > 0) {
    controlBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.textContent.trim();
            if (action === '涓婁竴璇?) {
                alert('璺宠浆鍒颁笂涓€璇?);
            } else if (action === '涓嬩竴璇?) {
                alert('璺宠浆鍒颁笅涓€璇?);
            } else if (action === '涓嬭浇瑙嗛') {
                alert('寮€濮嬩笅杞借棰?);
            }
        });
    });
}

// 缁冧範鎸夐挳鐐瑰嚮浜嬩欢
const exerciseBtns = document.querySelectorAll('.exercise-btn');
if (exerciseBtns.length > 0) {
    exerciseBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            alert('寮€濮嬬粌涔?);
        });
    });
}

// 鎿嶄綔鎸夐挳鐐瑰嚮浜嬩欢
const actionBtns = document.querySelectorAll('.action-btn');
if (actionBtns.length > 0) {
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.textContent.trim();
            if (action === '鍋氱瑪璁?) {
                alert('鎵撳紑绗旇缂栬緫鍣?);
            } else if (action === '涓嬭浇鏂囨。') {
                alert('寮€濮嬩笅杞芥枃妗?);
            }
        });
    });
}

// 璁ㄨ椤甸潰鍒濆鍖?function initDiscussionPage() {
    // 鏍囩椤靛垏鎹?    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tabId = this.dataset.tab;
                
                // 鏇存柊鏍囩鎸夐挳鐘舵€?                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // 鏇存柊鏍囩鍐呭
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
    
    // 鍒涘缓灏忕粍鎸夐挳鐐瑰嚮浜嬩欢
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
    
    // 鍏抽棴妯℃€佹
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
    
    // 鐐瑰嚮妯℃€佹澶栭儴鍏抽棴
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });
    
    // 鎻愪氦鍒涘缓灏忕粍
    if (submitCreateGroup) {
        submitCreateGroup.addEventListener('click', function() {
            const groupName = document.getElementById('group-name').value;
            const groupDescription = document.getElementById('group-description').value;
            
            if (!groupName) {
                alert('璇疯緭鍏ュ皬缁勫悕绉?);
                return;
            }
            
            // 鐢熸垚6浣嶉殢鏈虹紪鐮?            const groupCode = generateGroupCode();
            
            // 妯℃嫙鍒涘缓灏忕粍
            alert(`灏忕粍鍒涘缓鎴愬姛锛乗n灏忕粍鍚嶇О: ${groupName}\n灏忕粍缂栫爜: ${groupCode}`);
            
            // 鍏抽棴妯℃€佹
            if (createGroupModal) {
                createGroupModal.classList.remove('show');
            }
            
            // 娓呯┖琛ㄥ崟
            document.getElementById('group-name').value = '';
            document.getElementById('group-description').value = '';
        });
    }
    
    // 鍔犲叆灏忕粍鎸夐挳鐐瑰嚮浜嬩欢
    const joinGroupBtn = document.querySelector('.join-group-btn');
    const groupCodeInput = document.getElementById('group-code');
    
    if (joinGroupBtn) {
        joinGroupBtn.addEventListener('click', function() {
            const code = groupCodeInput.value.trim();
            
            if (!code) {
                alert('璇疯緭鍏ュ皬缁勭紪鐮?);
                return;
            }
            
            if (code.length !== 6) {
                alert('灏忕粍缂栫爜蹇呴』鏄?浣嶆暟瀛?);
                return;
            }
            
            // 妯℃嫙鍔犲叆灏忕粍
            alert(`鍔犲叆灏忕粍鎴愬姛锛乗n灏忕粍缂栫爜: ${code}`);
            
            // 娓呯┖杈撳叆
            groupCodeInput.value = '';
        });
    }
    
    // 杩涘叆灏忕粍鎸夐挳鐐瑰嚮浜嬩欢
    const enterGroupBtns = document.querySelectorAll('.enter-group-btn');
    const groupModal = document.getElementById('group-modal');
    
    if (enterGroupBtns.length > 0) {
        enterGroupBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const groupCard = this.closest('.group-card');
                const groupName = groupCard.querySelector('h4').textContent;
                const groupCode = groupCard.querySelector('.group-code').textContent.replace('缂栫爜: ', '');
                
                // 鏇存柊妯℃€佹鍐呭
                if (groupModal) {
                    document.getElementById('modal-title').textContent = groupName;
                    document.getElementById('modal-group-name').textContent = groupName;
                    document.getElementById('modal-group-code').textContent = groupCode;
                    groupModal.classList.add('show');
                }
            });
        });
    }
    
    // 灏忕粍鍐呭彂甯冨笘瀛?    const groupPostBtn = document.querySelector('.post-btn');
    const groupPostContent = document.getElementById('group-post-content');
    const groupPostsList = document.getElementById('group-posts-list');
    
    if (groupPostBtn) {
        groupPostBtn.addEventListener('click', function() {
            const content = groupPostContent.value.trim();
            
            if (!content) {
                alert('璇疯緭鍏ュ笘瀛愬唴瀹?);
                return;
            }
            
            // 鍒涘缓鏂板笘瀛?            const post = createPost(content);
            
            // 娣诲姞鍒板笘瀛愬垪琛?            if (groupPostsList) {
                groupPostsList.insertBefore(post, groupPostsList.firstChild);
            }
            
            // 娓呯┖杈撳叆
            groupPostContent.value = '';
        });
    }
    
    // 鍏叡璁哄潧鍙戝竷甯栧瓙
    const forumPostContent = document.getElementById('forum-post-content');
    const forumPostsList = document.getElementById('forum-posts-list');
    
    if (groupPostBtn) {
        groupPostBtn.addEventListener('click', function() {
            const content = forumPostContent ? forumPostContent.value.trim() : '';
            
            if (!content) {
                return;
            }
            
            // 鍒涘缓鏂板笘瀛?            const post = createPost(content);
            
            // 娣诲姞鍒板笘瀛愬垪琛?            if (forumPostsList) {
                forumPostsList.insertBefore(post, forumPostsList.firstChild);
            }
            
            // 娓呯┖杈撳叆
            if (forumPostContent) {
                forumPostContent.value = '';
            }
        });
    }
    
    // 鍥炲鎸夐挳鐐瑰嚮浜嬩欢
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
    
    // 鍥炲鎻愪氦
    const replySubmitBtns = document.querySelectorAll('.reply-submit');
    replySubmitBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const replyForm = this.closest('.reply-form');
            const replyInput = replyForm.querySelector('.reply-input');
            const content = replyInput.value.trim();
            
            if (!content) {
                alert('璇疯緭鍏ュ洖澶嶅唴瀹?);
                return;
            }
            
            // 鍒涘缓鏂板洖澶?            const reply = createReply(content);
            
            // 娣诲姞鍒板洖澶嶅垪琛?            const replies = replyForm.closest('.replies');
            replies.insertBefore(reply, replyForm);
            
            // 娓呯┖杈撳叆
            replyInput.value = '';
        });
    });
    
    // 鍒犻櫎甯栧瓙鎸夐挳鐐瑰嚮浜嬩欢
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-post-btn')) {
            if (confirm('纭畾瑕佸垹闄よ繖涓笘瀛愬悧锛?)) {
                const post = e.target.closest('.post');
                if (post) {
                    post.remove();
                }
            }
        }
    });
    
    // 鍒濆鍖朇odeMirror缂栬緫鍣紙濡傛灉瀛樺湪锛?    if (typeof CodeMirror !== 'undefined') {
        console.log('CodeMirror缂栬緫鍣ㄥ垵濮嬪寲鎴愬姛');
    }
}

// 鐢熸垚6浣嶉殢鏈哄皬缁勭紪鐮?function generateGroupCode() {
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += Math.floor(Math.random() * 10);
    }
    return code;
}

// 鍒涘缓甯栧瓙鍏冪礌
function createPost(content) {
    const post = document.createElement('div');
    post.className = 'post';
    
    const now = new Date();
    const timeString = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
    
    post.innerHTML = `
        <div class="post-header">
            <span class="post-author">${localStorage.getItem('username') || '0631250124'}</span>
            <span class="post-time">${timeString}</span>
            <button class="delete-post-btn">鍒犻櫎</button>
        </div>
        <div class="post-content">
            <p>${content}</p>
        </div>
        <div class="post-actions">
            <button class="reply-btn">鍥炲 (0)</button>
        </div>
        <div class="replies">
            <div class="reply-form">
                <textarea placeholder="鍥炲..." class="reply-input"></textarea>
                <button class="reply-submit">鍥炲</button>
            </div>
        </div>
    `;
    
    return post;
}

// 鍒涘缓鍥炲鍏冪礌
function createReply(content) {
    const reply = document.createElement('div');
    reply.className = 'reply';
    
    const now = new Date();
    const timeString = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
    
    reply.innerHTML = `
        <div class="reply-header">
            <span class="reply-author">${localStorage.getItem('username') || '0631250124'}</span>
            <span class="reply-time">${timeString}</span>
        </div>
        <div class="reply-content">
            <p>${content}</p>
        </div>
    `;
    
    return reply;
}

// 鍒濆鍖栬缃〉闈?function initSettingsPage() {
    const accountInput = document.getElementById('account');
    const nicknameInput = document.getElementById('nickname');
    const currentAvatar = document.querySelector('.current-avatar');
    const avatarInput = document.getElementById('avatar');
    const profileForm = document.getElementById('profileForm');
    const securityForm = document.getElementById('securityForm');
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    
    // 鏍囩椤靛垏鎹㈠姛鑳?    const tabBtns = document.querySelectorAll('.settings-tabs .tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 绉婚櫎鎵€鏈夋縺娲荤姸鎬?            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // 婵€娲诲綋鍓嶆爣绛?            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    if (accountInput) {
        // 涓嶈缃粯璁ゅ€硷紝浣跨敤妯℃澘娓叉煋鐨勫€?    }
    
    if (nicknameInput) {
        // 涓嶈缃粯璁ゅ€硷紝浣跨敤妯℃澘娓叉煋鐨勫€?    }
    
    if (currentAvatar) {
        // 涓嶈缃粯璁ゅ€硷紝浣跨敤妯℃澘娓叉煋鐨勫€?    }
    
    // 澶村儚涓婁紶鍔熻兘
    if (avatarInput && currentAvatar) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    currentAvatar.src = e.target.result;
                    
                    // 瀹炴椂鏇存柊鍙充笂瑙掔殑澶村儚
                    const headerAvatar = document.querySelector('.header-right .user-icon img');
                    if (headerAvatar) {
                        headerAvatar.src = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // 鏄电О杈撳叆瀹炴椂鏇存柊
    if (nicknameInput) {
        nicknameInput.addEventListener('input', function() {
            const nickname = this.value.trim();
            if (nickname) {
                // 瀹炴椂鏇存柊鍙充笂瑙掔殑鏄电О
                const greetingElement = document.querySelector('.header-right .greeting p:first-child');
                if (greetingElement) {
                    // 淇濈暀闂€欒閮ㄥ垎锛屽彧鏇存柊鏄电О
                    const text = greetingElement.textContent;
                    const greetingPart = text.split('锛?)[0];
                    greetingElement.textContent = `${greetingPart}锛?{nickname}`;
                }
            }
        });
    }
    
    // 鍩烘湰璧勬枡琛ㄥ崟鎻愪氦鍔熻兘 - 璁╄〃鍗曟甯告彁浜ゅ埌鏈嶅姟鍣?    if (profileForm) {
        // 涓嶆嫤鎴〃鍗曟彁浜わ紝璁〧lask鍚庣澶勭悊
    }
    
    // 瀵嗙爜淇敼鍔熻兘
    if (securityForm) {
        securityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (!currentPassword) {
                showNotification('璇疯緭鍏ュ綋鍓嶅瘑鐮侊紒', 'error');
                return;
            }
            
            if (!newPassword) {
                showNotification('璇疯緭鍏ユ柊瀵嗙爜锛?, 'error');
                return;
            }
            
            if (newPassword.length < 6) {
                showNotification('鏂板瘑鐮侀暱搴︿笉鑳藉皯浜?浣嶏紒', 'error');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                showNotification('涓ゆ杈撳叆鐨勫瘑鐮佷笉涓€鑷达紒', 'error');
                return;
            }
            
            // 妯℃嫙瀵嗙爜淇敼鎴愬姛
            showNotification('瀵嗙爜淇敼鎴愬姛锛?, 'success');
            securityForm.reset();
        });
    }
    
    // 璐︽埛娉ㄩ攢鍔熻兘
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function() {
            if (confirm('纭畾瑕佹敞閿€璐︽埛鍚楋紵姝ゆ搷浣滀笉鍙仮澶嶏紝鎵€鏈夋暟鎹皢琚案涔呭垹闄ゃ€?)) {
                // 娓呴櫎鏈湴瀛樺偍
                localStorage.clear();
                showNotification('璐︽埛宸叉敞閿€锛?, 'success');
                
                // 寤惰繜璺宠浆鍒扮櫥褰曢〉闈?                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
            }
        });
    }
}

// 鏄剧ず閫氱煡娑堟伅
function showNotification(message, type = 'info') {
    // 鍒涘缓閫氱煡鍏冪礌
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 娣诲姞鏍峰紡
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
    
    // 鏍规嵁绫诲瀷璁剧疆鑳屾櫙鑹?    switch (type) {
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
    
    // 娣诲姞鍒伴〉闈?    document.body.appendChild(notification);
    
    // 鏄剧ず閫氱煡
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 3绉掑悗闅愯棌閫氱煡
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 璁剧疆椤甸潰鍔熻兘
// 鍙湁鍦ㄨ缃〉闈㈡墠鍒濆鍖?if (window.location.pathname.includes('settings')) {
    initSettingsPage();
}

// 杩愯浠ｇ爜
function runCode() {
    const codeEditor = document.getElementById('codeEditor');
    const outputPane = document.getElementById('outputPane');
    const errorList = document.getElementById('errorList');
    const knowledgeList = document.getElementById('knowledgeList');
    
    if (!codeEditor) return;
    
    const code = codeEditor.value.trim();
    
    if (!code) {
        alert('璇疯緭鍏ユ垨涓婁紶浠ｇ爜');
        return;
    }
    
    // 娓呯┖涔嬪墠鐨勭粨鏋?    if (outputPane) {
        outputPane.innerHTML = '<div class="vs-output-placeholder"><p>姝ｅ湪杩愯浠ｇ爜...</p></div>';
    }
    if (errorList) {
        errorList.innerHTML = '<div class="vs-errors-placeholder"><p>姝ｅ湪鍒嗘瀽浠ｇ爜...</p></div>';
    }
    if (knowledgeList) {
        knowledgeList.innerHTML = '<div class="vs-knowledge-placeholder"><p>姝ｅ湪鍏宠仈鐭ヨ瘑鐐?..</p></div>';
    }
    
    // 妯℃嫙浠ｇ爜杩愯鍜屽垎鏋?    setTimeout(() => {
        const result = analyzeCode(code);
        displayResults(result);
    }, 1000);
}

// 鍒嗘瀽浠ｇ爜
function analyzeCode(code) {
    const errors = [];
    const warnings = [];
    
    // 妫€鏌ヨ娉曢敊璇?    const syntaxErrors = checkSyntaxErrors(code);
    errors.push(...syntaxErrors);
    
    // 妫€鏌ュ父瑙侀敊璇?    const commonErrors = checkCommonErrors(code);
    errors.push(...commonErrors.errors);
    warnings.push(...commonErrors.warnings);
    
    // 鐢熸垚杩愯缁撴灉
    const output = generateOutput(code, errors);
    
    return {
        output,
        errors,
        warnings
    };
}

// 妫€鏌ヨ娉曢敊璇?function checkSyntaxErrors(code) {
    const errors = [];
    const lines = code.split('\n');
    
    // 鍏ㄥ眬鎷彿璁℃暟
    let totalOpenBraces = 0;
    let totalCloseBraces = 0;
    let totalOpenParens = 0;
    let totalCloseParens = 0;
    
    lines.forEach((line, index) => {
        const lineNum = index + 1;
        const trimmedLine = line.trim();
        
        // 璺宠繃绌鸿鍜屾敞閲?        if (!trimmedLine || trimmedLine.startsWith('//') || trimmedLine.startsWith('#')) {
            return;
        }
        
        // 妫€鏌ョ己灏戝垎鍙?- 鍙鏌ョ湡姝ｇ殑璇彞琛?        const isStatementLine = !trimmedLine.endsWith('{') && !trimmedLine.endsWith('}') && 
                              !trimmedLine.includes('for(') && !trimmedLine.includes('if(') && 
                              !trimmedLine.includes('while(') && !trimmedLine.includes('switch(') && 
                              !trimmedLine.includes('do') && !trimmedLine.includes('case') && 
                              !trimmedLine.includes('default') && !trimmedLine.includes('return') && 
                              !trimmedLine.includes('break') && !trimmedLine.includes('continue');
        
        if (isStatementLine && !trimmedLine.endsWith(';')) {
            // 杩涗竴姝ユ鏌ユ槸鍚︽槸鍑芥暟澹版槑鎴栧叾浠栦笉闇€瑕佸垎鍙风殑缁撴瀯
            const isFunctionDeclaration = trimmedLine.includes('(') && trimmedLine.includes(')') && 
                                         (trimmedLine.includes('void') || trimmedLine.includes('int') || 
                                          trimmedLine.includes('float') || trimmedLine.includes('double') || 
                                          trimmedLine.includes('bool') || trimmedLine.includes('char'));
            
            if (!isFunctionDeclaration) {
                errors.push({
                    type: 'error',
                    location: `绗?{lineNum}琛宍,
                    message: '缂哄皯鍒嗗彿',
                    suggestion: '鍦ㄨ鍙ユ湯灏炬坊鍔犲垎鍙?(;)'
                });
            }
        }
        
        // 绱鎷彿璁℃暟
        totalOpenBraces += (line.match(/{/g) || []).length;
        totalCloseBraces += (line.match(/}/g) || []).length;
        totalOpenParens += (line.match(/\(/g) || []).length;
        totalCloseParens += (line.match(/\)/g) || []).length;
    });
    
    // 妫€鏌ュ叏灞€鎷彿鍖归厤
    if (totalOpenBraces > totalCloseBraces) {
        errors.push({
            type: 'error',
            location: '鍏ㄥ眬',
            message: '缂哄皯闂悎澶ф嫭鍙?,
            suggestion: '娣诲姞缂哄け鐨勯棴鍚堝ぇ鎷彿 (})'
        });
    } else if (totalOpenBraces < totalCloseBraces) {
        errors.push({
            type: 'error',
            location: '鍏ㄥ眬',
            message: '澶氫綑鐨勯棴鍚堝ぇ鎷彿',
            suggestion: '绉婚櫎澶氫綑鐨勯棴鍚堝ぇ鎷彿 (})'
        });
    }
    
    if (totalOpenParens > totalCloseParens) {
        errors.push({
            type: 'error',
            location: '鍏ㄥ眬',
            message: '缂哄皯闂悎鍦嗘嫭鍙?,
            suggestion: '娣诲姞缂哄け鐨勯棴鍚堝渾鎷彿 ())'
        });
    } else if (totalOpenParens < totalCloseParens) {
        errors.push({
            type: 'error',
            location: '鍏ㄥ眬',
            message: '澶氫綑鐨勯棴鍚堝渾鎷彿',
            suggestion: '绉婚櫎澶氫綑鐨勯棴鍚堝渾鎷彿 ())'
        });
    }
    
    return errors;
}

// 妫€鏌ュ父瑙侀敊璇?function checkCommonErrors(code) {
    const errors = [];
    const warnings = [];
    
    // 妫€鏌ユ湭鍒濆鍖栫殑鍙橀噺
    const uninitializedVars = code.match(/int\s+\w+\s*;/g) || [];
    uninitializedVars.forEach(match => {
        warnings.push({
            type: 'warning',
            location: '鍏ㄥ眬',
            message: '鍙橀噺鍙兘鏈垵濮嬪寲',
            suggestion: '寤鸿鍦ㄤ娇鐢ㄥ彉閲忓墠杩涜鍒濆鍖?
        });
    });
    
    // 妫€鏌ュ唴瀛樻硠婕忛闄?    if (code.includes('new ') && !code.includes('delete ')) {
        errors.push({
            type: 'error',
            location: '鍏ㄥ眬',
            message: '鍙兘鐨勫唴瀛樻硠婕?,
            suggestion: '浣跨敤new鍒嗛厤鐨勫唴瀛樺簲璇ヤ娇鐢╠elete閲婃斁'
        });
    }
    
    // 妫€鏌ユ暟缁勮秺鐣岄闄?    if (code.includes('for') && code.includes('[i]')) {
        warnings.push({
            type: 'warning',
            location: '寰幆',
            message: '鍙兘鐨勬暟缁勮秺鐣?,
            suggestion: '纭繚寰幆鍙橀噺鍦ㄦ暟缁勮寖鍥村唴'
        });
    }
    
    // 妫€鏌ユ寚閽堟湭鍒濆鍖?    if (code.includes('*') && !code.includes('= nullptr') && !code.includes('= NULL')) {
        warnings.push({
            type: 'warning',
            location: '鎸囬拡',
            message: '鎸囬拡鍙兘鏈垵濮嬪寲',
            suggestion: '寤鸿灏嗘寚閽堝垵濮嬪寲涓簄ullptr'
        });
    }
    
    // 妫€鏌ユ湭浣跨敤鐨勫彉閲?    const varDeclarations = code.match(/int\s+(\w+)/g) || [];
    varDeclarations.forEach(decl => {
        const varName = decl.replace('int ', '');
        const usageCount = (code.match(new RegExp(varName, 'g')) || []).length;
        if (usageCount <= 1) {
            warnings.push({
                type: 'warning',
                location: '鍙橀噺澹版槑',
                message: `鍙橀噺 ${varName} 鍙兘鏈娇鐢╜,
                suggestion: '妫€鏌ユ槸鍚﹂渶瑕佷娇鐢ㄨ鍙橀噺鎴栧垹闄ゅ０鏄?
            });
        }
    });
    
    return { errors, warnings };
}

// 鐢熸垚杈撳嚭缁撴灉
function generateOutput(code, errors) {
    if (errors.length > 0) {
        return '缂栬瘧澶辫触锛乗n璇锋煡鐪嬮敊璇俊鎭簡瑙ｈ鎯呫€?;
    }
    
    let output = '缂栬瘧鎴愬姛锛乗n\n';
    
    if (code.includes('cout')) {
        output += '绋嬪簭杈撳嚭:\n';
        const coutMatches = code.match(/cout\s*<<\s*([^;]+);/g) || [];
        coutMatches.forEach(match => {
            const content = match.replace(/cout\s*<<\s*/, '').replace(/;/, '');
            if (content.includes('"')) {
                output += content.replace(/"/g, '') + '\n';
            } else {
                output += `[鍙橀噺鍊? ${content.trim()}]\n`;
            }
        });
    } else {
        output += '绋嬪簭缂栬瘧鎴愬姛锛屼絾娌℃湁杈撳嚭銆俓n';
        output += '鎻愮ず: 浣跨敤cout璇彞鏉ヨ緭鍑虹粨鏋溿€?;
    }
    
    return output;
}

// 鏄剧ず缁撴灉
function displayResults(result) {
    const outputPane = document.getElementById('outputPane');
    const errorList = document.getElementById('errorList');
    const knowledgeList = document.getElementById('knowledgeList');
    
    // 鏄剧ず杩愯缁撴灉
    if (outputPane) {
        outputPane.innerHTML = `<div class="output-content-text">${escapeHtml(result.output)}</div>`;
    }
    
    // 鏄剧ず閿欒淇℃伅
    const allErrors = [...result.errors, ...result.warnings];
    if (allErrors.length > 0) {
        if (errorList) {
            errorList.innerHTML = '';
            allErrors.forEach(error => {
                const errorItem = document.createElement('div');
                errorItem.className = `error-item ${error.type}`;
                errorItem.innerHTML = `
                    <div class="error-header">
                        <span class="error-type">${error.type === 'error' ? '閿欒' : '璀﹀憡'}</span>
                        <span class="error-location">${escapeHtml(error.location)}</span>
                    </div>
                    <p class="error-message">${escapeHtml(error.message)}</p>
                    <p class="error-suggestion">馃挕 寤鸿: ${escapeHtml(error.suggestion)}</p>
                `;
                errorList.appendChild(errorItem);
            });
        }
    } else {
        if (errorList) {
            errorList.innerHTML = '<div class="vs-errors-placeholder"><p>鉁?浠ｇ爜娌℃湁鍙戠幇閿欒</p></div>';
        }
    }
}

// HTML杞箟
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 鎼滅储鍔熻兘
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

    // 鍥炶溅閿悳绱?    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }
}

// 鍒濆鍖栬璁洪〉闈㈠姛鑳?if (window.location.pathname.includes('community')) {
    initDiscussionPage();
}
