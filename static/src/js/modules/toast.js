/**
 * Toast通知组件 - 全局消息提示管理器
 * 提供成功、错误、警告、信息四种类型的通知提示
 * @module toast
 */

import { escapeHtml } from './utils.js';

/**
 * Toast通知管理器类 - 管理全局Toast通知的显示与隐藏
 * @class ToastManager
 */
export class ToastManager {
  constructor() {
    /** @type {HTMLElement|null} Toast容器元素 */
    this.container = null;
    this.init();
  }

  /**
   * 初始化Toast容器，确保页面中存在唯一的toast-container
   * @private
   */
  init() {
    if (!document.querySelector('.toast-container')) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.setAttribute('role', 'status');
      this.container.setAttribute('aria-live', 'polite');
      document.body.appendChild(this.container);
    } else {
      this.container = document.querySelector('.toast-container');
    }
  }

  /**
   * 显示一条Toast通知消息
   * @param {string} message - 通知内容文本
   * @param {'success'|'error'|'warning'|'info'} [type='info'] - 通知类型
   * @param {number} [duration=3000] - 显示时长（毫秒），0表示不自动关闭
   * @returns {HTMLElement|null} 创建的Toast元素，失败时返回null
   */
  show(message, type = 'info', duration = 3000) {
    try {
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.setAttribute('role', 'alert');

      const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
      };

      toast.innerHTML = `
        <i class="fas ${iconMap[type] || 'fa-info-circle'}" aria-hidden="true"></i>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close" aria-label="关闭通知">&times;</button>
      `;

      this.container.appendChild(toast);

      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          toast.classList.add('show');
        });
      });

      if (duration > 0) {
        setTimeout(() => this.dismiss(toast), duration);
      }

      const closeBtn = toast.querySelector('.toast-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => {
          this.dismiss(toast);
        });
      }

      return toast;
    } catch (error) {
      console.error('Toast显示失败:', error);
      return null;
    }
  }

  /**
   * 显示成功类型的通知（快捷方法）
   * @param {string} message - 通知内容
   * @param {number} [duration=3000] - 显示时长
   * @returns {HTMLElement|null}
   */
  success(message, duration = 3000) {
    return this.show(message, 'success', duration);
  }

  /**
   * 显示错误类型的通知（快捷方法）
   * @param {string} message - 通知内容
   * @param {number} [duration=4000] - 显示时长
   * @returns {HTMLElement|null}
   */
  error(message, duration = 4000) {
    return this.show(message, 'error', duration);
  }

  /**
   * 显示警告类型的通知（快捷方法）
   * @param {string} message - 通知内容
   * @param {number} [duration=3500] - 显示时长
   * @returns {HTMLElement|null}
   */
  warning(message, duration = 3500) {
    return this.show(message, 'warning', duration);
  }

  /**
   * 显示信息类型的通知（快捷方法）
   * @param {string} message - 通知内容
   * @param {number} [duration=3000] - 显示时长
   * @returns {HTMLElement|null}
   */
  info(message, duration = 3000) {
    return this.show(message, 'info', duration);
  }

  /**
   * 关闭指定的Toast通知
   * @param {HTMLElement} toastEl - 要关闭的Toast DOM元素
   */
  dismiss(toastEl) {
    if (!toastEl || !toastEl.parentNode) return;

    toastEl.classList.remove('show');
    toastEl.classList.add('hide');

    setTimeout(() => {
      if (toastEl.parentNode) {
        toastEl.remove();
      }
    }, 300);
  }

  /**
   * 清除所有当前显示的Toast通知
   */
  clear() {
    if (!this.container) return;
    const toasts = this.container.querySelectorAll('.toast');
    toasts.forEach((t) => this.dismiss(t));
  }

  /**
   * 内部HTML转义方法（使用utils中的escapeHtml作为备选）
   * @private
   * @param {string} text - 需要转义的文本
   * @returns {string}
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
