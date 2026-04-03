/**
 * 移动端菜单组件 - 响应式侧边栏菜单控制器
 * 在小屏幕设备上提供汉堡菜单和滑出式导航
 * @module mobile-menu
 */

/**
 * MobileMenu类 - 管理移动端侧边栏的展开/收起交互
 * @class MobileMenu
 */
export class MobileMenu {
  constructor() {
    /** @type {HTMLElement|null} 侧边栏元素 */
    this.sidebar = null;
    /** @type {HTMLButtonElement|null} 汉堡菜单按钮 */
    this.toggleBtn = null;
    /** @type {HTMLElement|null} 背景遮罩层 */
    this.overlay = null;
    /** @type {boolean} 菜单当前是否展开 */
    this.isOpen = false;
    /** @type {number} 断点阈值（像素） */
    this.breakpoint = 768;

    this.init();
  }

  /**
   * 初始化移动端菜单：查找/创建DOM元素并绑定事件
   */
  init() {
    this.sidebar = document.querySelector('.sidebar');

    if (!this.sidebar) return;

    this.createToggleButton();
    this.createOverlay();
    this.bindEvents();
    this.updateOnResize();
  }

  /**
   * 创建汉堡菜单切换按钮并插入到header中
   * @private
   */
  createToggleButton() {
    if (document.querySelector('.mobile-menu-toggle')) return;

    this.toggleBtn = document.createElement('button');
    this.toggleBtn.className = 'mobile-menu-toggle';
    this.toggleBtn.setAttribute('aria-label', '打开菜单');
    this.toggleBtn.setAttribute('aria-expanded', 'false');
    this.toggleBtn.setAttribute('type', 'button');
    this.toggleBtn.innerHTML = `
      <span class="hamburger-line"></span>
      <span class="hamburger-line"></span>
      <span class="hamburger-line"></span>
    `;

    const header = document.querySelector('.header');
    if (header) {
      header.appendChild(this.toggleBtn);
    }
  }

  /**
   * 创建点击关闭用的背景遮罩层
   * @private
   */
  createOverlay() {
    if (document.querySelector('.mobile-menu-overlay')) return;

    this.overlay = document.createElement('div');
    this.overlay.className = 'mobile-menu-overlay';
    this.overlay.setAttribute('aria-hidden', 'true');
    document.body.appendChild(this.overlay);
  }

  /**
   * 绑定所有事件监听器（按钮点击、遮罩点击、ESC键）
   * @private
   */
  bindEvents() {
    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => this.toggle());
    }

    if (this.overlay) {
      this.overlay.addEventListener('click', () => this.close());
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }

  /**
   * 切换菜单的展开/收起状态
   */
  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  /**
   * 打开移动端菜单
   */
  open() {
    if (this.isOpen) return;
    this.isOpen = true;

    this.sidebar?.classList.add('open');
    this.overlay?.classList.add('show');
    this.toggleBtn?.classList.add('active');
    this.toggleBtn?.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';

    if (this.toggleBtn) {
      this.toggleBtn.setAttribute('aria-label', '关闭菜单');
    }
  }

  /**
   * 关闭移动端菜单
   */
  close() {
    if (!this.isOpen) return;
    this.isOpen = false;

    this.sidebar?.classList.remove('open');
    this.overlay?.classList.remove('show');
    this.toggleBtn?.classList.remove('active');
    this.toggleBtn?.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';

    if (this.toggleBtn) {
      this.toggleBtn.setAttribute('aria-label', '打开菜单');
    }
  }

  /**
   * 监听窗口resize事件，在大屏幕时自动关闭菜单
   * 使用内联debounce避免循环依赖
   * @private
   */
  updateOnResize() {
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (window.innerWidth > this.breakpoint && this.isOpen) {
          this.close();
        }
      }, 250);
    });
  }

  /**
   * 销毁实例，移除所有创建的DOM元素和事件监听
   */
  destroy() {
    this.close();
    this.toggleBtn?.remove();
    this.overlay?.remove();
    this.toggleBtn = null;
    this.overlay = null;
  }
}
