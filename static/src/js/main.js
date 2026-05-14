/**
 * 主入口文件 - 初始化所有前端模块并导出全局实例
 * @module main
 */

// 导入SCSS设计系统
import '@/scss/main.scss';

// 导入核心功能模块
import { ToastManager } from './modules/toast.js';
import { LoadingManager } from './modules/loading.js';
import { MobileMenu } from './modules/mobile-menu.js';

// 初始化全局单例实例
const toast = new ToastManager();
const loading = new LoadingManager();
const mobileMenu = new MobileMenu();

// 挂载到window对象供全局使用（模板内联脚本可访问）
window.toast = toast;
window.loading = loading;
window.mobileMenu = mobileMenu;

// DOM加载完成后输出就绪信息
console.log('✅ Frontend modules initialized');
console.log('📦 Modules loaded: Toast, Loading, MobileMenu');
