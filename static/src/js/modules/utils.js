/**
 * 基础工具模块 - 提供DOM操作、安全防护、性能优化等通用工具函数
 * @module utils
 */

/**
 * DOM查询快捷方法 - 查找匹配选择器的第一个元素
 * @param {string} selector - CSS选择器
 * @param {Element|Document} [context=document] - 查询上下文
 * @returns {Element|null} 匹配的DOM元素或null
 */
export const $ = (selector, context = document) =>
  context.querySelector(selector);

/**
 * DOM批量查询方法 - 查找匹配选择器的所有元素
 * @param {string} selector - CSS选择器
 * @param {Element|Document} [context=document] - 查询上下文
 * @returns {Element[]} 匹配的DOM元素数组
 */
export const $$ = (selector, context = document) =>
  [...context.querySelectorAll(selector)];

/**
 * XSS防护 - 转义HTML特殊字符，防止XSS攻击
 * @param {string} str - 需要转义的字符串
 * @returns {string} 转义后的安全字符串
 */
export function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return str.replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * 防抖函数 - 限制高频事件触发，只在最后一次调用后延迟执行
 * @param {Function} fn - 需要防抖的函数
 * @param {number} [delay=300] - 延迟时间（毫秒）
 * @returns {Function} 防抖处理后的函数
 */
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * 节流函数 - 保证固定间隔执行，忽略间隔内的重复调用
 * @param {Function} fn - 需要节流的函数
 * @param {number} [interval=300] - 执行间隔（毫秒）
 * @returns {Function} 节流处理后的函数
 */
export function throttle(fn, interval = 300) {
  let lastTime = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

/**
 * 时间格式化工具 - 将日期对象格式化为指定格式的字符串
 * 支持的格式占位符：YYYY(年), MM(月), DD(日), HH(时), mm(分), ss(秒)
 * @param {Date|string|number} date - 日期对象、时间戳或日期字符串
 * @param {string} [format='YYYY-MM-DD HH:mm:ss'] - 目标格式
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  try {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';

    const pad = (n) => String(n).padStart(2, '0');

    const tokens = {
      'YYYY': d.getFullYear(),
      'MM': pad(d.getMonth() + 1),
      'DD': pad(d.getDate()),
      'HH': pad(d.getHours()),
      'mm': pad(d.getMinutes()),
      'ss': pad(d.getSeconds())
    };

    let result = format;
    for (const [token, value] of Object.entries(tokens)) {
      result = result.replace(token, value);
    }
    return result;
  } catch (e) {
    console.warn('FormatDate error:', e);
    return '';
  }
}

/**
 * 安全的本地存储封装（不存储敏感信息）
 * 提供带错误处理的localStorage读写操作
 * @namespace storage
 */
export const storage = {
  /**
   * 从localStorage读取数据并自动JSON解析
   * @param {string} key - 存储键名
   * @param {*} [defaultValue=null] - 读取失败或不存在时的默认返回值
   * @returns {*} 解析后的数据或默认值
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
      console.warn('Storage get error:', e);
      return defaultValue;
    }
  },

  /**
   * 将数据序列化后写入localStorage
   * @param {string} key - 存储键名
   * @param {*} value - 需要存储的数据（会被JSON序列化）
   * @returns {boolean} 是否存储成功
   */
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.warn('Storage set error:', e);
      return false;
    }
  },

  /**
   * 从localStorage删除指定键的数据
   * @param {string} key - 要删除的键名
   * @returns {boolean} 是否删除成功
   */
  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      return false;
    }
  }
};
