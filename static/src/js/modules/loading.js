/**
 * 加载状态管理器 - 管理全屏加载遮罩和按钮加载状态
 * @module loading
 */

/**
 * LoadingManager类 - 控制全局加载动画和按钮级加载反馈
 * @class LoadingManager
 */
export class LoadingManager {
  constructor() {
    /** @type {HTMLElement|null} 全屏加载遮罩层 */
    this.overlay = null;
    /** @type {number} 当前活跃的loading计数器 */
    this._counter = 0;
    this.initGlobalLoading();
  }

  /**
   * 初始化全局Loading遮罩层DOM结构
   * @private
   */
  initGlobalLoading() {
    if (!document.querySelector('.loading-overlay')) {
      this.overlay = document.createElement('div');
      this.overlay.className = 'loading-overlay';
      this.overlay.setAttribute('role', 'progressbar');
      this.overlay.setAttribute('aria-label', '加载中');
      this.overlay.innerHTML = `
        <div class="loading-spinner">
          <div class="spinner-circle"></div>
          <p class="loading-text">加载中...</p>
        </div>
      `;
      this.overlay.style.display = 'none';
      document.body.appendChild(this.overlay);
    } else {
      this.overlay = document.querySelector('.loading-overlay');
    }
  }

  /**
   * 显示全屏加载遮罩（支持计数器嵌套调用）
   * @param {Object} [options={}] - 配置选项
   * @param {string} [options.text='加载中...'] - 加载提示文字
   */
  show(options = {}) {
    const { text = '加载中...' } = options;
    this._counter++;

    if (this.overlay) {
      const textEl = this.overlay.querySelector('.loading-text');
      if (textEl) textEl.textContent = text;
      this.overlay.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }

  /**
   * 隐藏全屏加载遮罩（计数器归零时才真正隐藏）
   */
  hide() {
    this._counter = Math.max(0, this._counter - 1);

    if (this._counter <= 0 && this.overlay) {
      this._counter = 0;
      this.overlay.style.display = 'none';
      document.body.style.overflow = '';
    }
  }

  /**
   * 重置计数器并强制隐藏加载遮罩
   */
  forceHide() {
    this._counter = 0;
    if (this.overlay) {
      this.overlay.style.display = 'none';
      document.body.style.overflow = '';
    }
  }

  /**
   * 将按钮切换为加载状态（禁用+旋转图标）
   * @param {HTMLButtonElement|HTMLInputElement|null} btnElement - 目标按钮元素
   */
  showButtonLoading(btnElement) {
    if (!btnElement) return;

    btnElement.disabled = true;
    btnElement.dataset.originalText = btnElement.textContent || btnElement.innerText || '';
    btnElement.innerHTML = `
      <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
      <span>处理中...</span>
    `;
    btnElement.classList.add('btn-loading');
  }

  /**
   * 将按钮从加载状态恢复为原始状态
   * @param {HTMLButtonElement|HTMLInputElement|null} btnElement - 目标按钮元素
   */
  hideButtonLoading(btnElement) {
    if (!btnElement) return;

    btnElement.disabled = false;
    btnElement.textContent = btnElement.dataset.originalText || '提交';
    btnElement.classList.remove('btn-loading');
    delete btnElement.dataset.originalText;
  }

  /**
   * 异步包装器 - 自动在异步操作前后控制loading状态
   * @param {Function} asyncFn - 异步函数
   * @param {Object} [options={}] - show方法的配置项
   * @returns {Promise} asyncFn执行结果
   */
  async wrap(asyncFn, options = {}) {
    this.show(options);
    try {
      const result = await asyncFn();
      return result;
    } finally {
      this.hide();
    }
  }
}
