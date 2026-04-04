#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Koyeb 部署前检查脚本
=====================

使用方法：
  python check_deployment.py          # 检查当前环境
  python check_deployment.py --fix     # 尝试自动修复问题
  python check_deployment.py --env .env.production  # 指定环境变量文件

功能：
  - 验证必需的环境变量
  - 测试数据库连接
  - 检查依赖是否安装
  - 验证配置文件完整性
  - 生成部署报告
"""

import os
import sys
import json
from datetime import datetime

class DeploymentChecker:
    def __init__(self, env_file=None):
        self.env_file = env_file
        self.issues = []
        self.warnings = []
        self.successes = []
        
        if env_file and os.path.exists(env_file):
            self.load_env_file(env_file)
    
    def load_env_file(self, filepath):
        """从文件加载环境变量"""
        print(f"📂 从 {filepath} 加载环境变量...")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✓ 环境变量加载完成\n")
    
    def print_header(self, title):
        """打印标题"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60 + "\n")
    
    def check_required_vars(self):
        """检查必需的环境变量"""
        self.print_header("1️⃣  检查必需环境变量")
        
        required_vars = {
            'SECRET_KEY': 'Flask Session 密钥',
            'MYSQL_HOST': 'MySQL 主机地址',
            'MYSQL_USER': 'MySQL 用户名',
            'MYSQL_PASSWORD': 'MySQL 密码',
            'MYSQL_DATABASE': 'MySQL 数据库名'
        }
        
        all_ok = True
        
        for var_name, description in required_vars.items():
            value = os.environ.get(var_name, '')
            
            if not value:
                self.issues.append(f"❌ 缺少: {var_name} ({description})")
                all_ok = False
            elif var_name == 'SECRET_KEY' and len(value) < 32:
                self.warnings.append(f"⚠️  {var_name} 长度不足（建议 ≥ 32 字符，当前: {len(value)}）")
                all_ok = False
            else:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
                self.successes.append(f"✅ {var_name}: {masked_value}")
        
        return all_ok
    
    def check_optional_vars(self):
        """检查可选的环境变量"""
        self.print_header("2️⃣  检查可选环境变量")
        
        optional_vars = {
            'OLLAMA_BASE_URL': 'AI 模型服务 URL',
            'OLLAMA_MODEL': 'AI 模型名称',
            'BAIDU_OCR_API_KEY': '百度 OCR API Key',
            'GEMINI_API_KEY': 'Gemini API Key',
            'FLASK_ENV': '运行环境'
        }
        
        for var_name, description in optional_vars.items():
            value = os.environ.get(var_name, '')
            
            if not value:
                self.warnings.append(f"⏭️  未设置: {var_name} ({description}) - 使用默认值")
            else:
                if 'KEY' in var_name or 'PASSWORD' in var_name:
                    display_value = value[:4] + '****' if len(value) > 4 else '****'
                else:
                    display_value = value
                
                self.successes.append(f"✅ {var_name}: {display_value}")
    
    def test_database_connection(self):
        """测试数据库连接"""
        self.print_header("3️⃣  测试数据库连接")
        
        try:
            import mysql.connector
            
            host = os.getenv('MYSQL_HOST')
            user = os.getenv('MYSQL_USER')
            password = os.getenv('MYSQL_PASSWORD')
            database = os.getenv('MYSQL_DATABASE')
            port = int(os.getenv('MYSQL_PORT', '3306'))
            
            if not all([host, user, password, database]):
                self.issues.append("❌ 数据库配置不完整，无法测试连接")
                return False
            
            print(f"正在连接 {host}:{port}/{database} ...")
            
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            conn.close()
            
            self.successes.append(f"✅ 数据库连接成功 (MySQL {version})")
            self.successes.append(f"✅ 当前表数量: {len(tables)}")
            
            return True
            
        except ImportError:
            self.warnings.append("⚠️  mysql-connector-python 未安装，跳过数据库测试")
            return None
        except Exception as e:
            self.issues.append(f"❌ 数据库连接失败: {str(e)}")
            return False
    
    def check_dependencies(self):
        """检查 Python 依赖"""
        self.print_header("4️⃣  检查 Python 依赖")
        
        required_packages = [
            ('flask', 'Flask'),
            ('flask_login', 'Flask-Login'),
            ('flask_caching', 'Flask-Caching'),
            ('flask_limiter', 'Flask-Limiter'),
            ('mysql.connector', 'mysql-connector-python'),
            ('PIL', 'Pillow'),
            ('requests', 'requests'),
        ]
        
        optional_packages = [
            ('weasyprint', 'WeasyPrint (PDF 导出)'),
            ('reportlab', 'ReportLab (备用 PDF)'),
        ]
        
        for module, name in required_packages:
            try:
                __import__(module)
                self.successes.append(f"✅ {name} 已安装")
            except ImportError:
                self.issues.append(f"❌ {name} 未安装 (pip install {name.lower().replace('-', '_')})")
        
        for module, name in optional_packages:
            try:
                __import__(module)
                self.successes.append(f"✅ {name} 已安装")
            except ImportError:
                self.warnings.append(f"⏭️  {name} 未安装 (可选)")
    
    def check_compiler(self):
        """检查 C++ 编译器"""
        self.print_header("5️⃣  检查 C++ 编译器")
        
        import shutil
        import platform
        
        gpp_path = shutil.which('g++')
        
        if gpp_path:
            try:
                result = os.popen(f'{gpp_path} --version').read()
                version = result.split('\n')[0] if result else '未知版本'
                self.successes.append(f"✅ G++ 编译器已安装: {gpp_path}")
                self.successes.append(f"   版本信息: {version}")
            except Exception as e:
                self.warnings.append(f"⚠️  找到 G++ 但获取版本失败: {e}")
        else:
            if platform.system() == 'Windows':
                self.warnings.append("⚠️  Windows 系统：请确保已安装 MinGW-w64 并添加到 PATH")
            else:
                self.warnings.append("ℹ️  Linux/Docker 环境：Dockerfile 中已包含 g++ 安装命令")
    
    def check_config_files(self):
        """检查配置文件完整性"""
        self.print_header("6️⃣  检查配置文件")
        
        required_files = [
            'app/config.py',
            'app/__init__.py',
            'run.py',
            'gunicorn.conf.py',
            'Dockerfile',
            'requirements.txt',
        ]
        
        for filepath in required_files:
            if os.path.exists(filepath):
                self.successes.append(f"✅ {filepath} 存在")
            else:
                self.issues.append(f"❌ {filepath} 不存在")
    
    def generate_report(self):
        """生成检查报告"""
        self.print_header("📊 检查报告摘要")
        
        print(f"\n{'='*60}")
        print(f"  ✅ 成功项: {len(self.successes)}")
        print(f"  ⚠️  警告项: {len(self.warnings)}")
        print(f"  ❌ 错误项: {len(self.issues)}")
        print(f"{'='*60}\n")
        
        if self.successes:
            print("✅ 成功项:")
            for item in self.successes:
                print(f"   {item}")
            print()
        
        if self.warnings:
            print("⚠️  警告项（不影响部署，但建议修复）:")
            for item in self.warnings:
                print(f"   {item}")
            print()
        
        if self.issues:
            print("❌ 错误项（必须修复才能部署）:")
            for item in self.issues:
                print(f"   {item}")
            print()
        
        is_ready = len(self.issues) == 0
        
        if is_ready:
            print("🎉 恭喜！所有必需项检查通过，可以部署到 Koyeb！\n")
            print("下一步操作：")
            print("  1. 将代码推送到 GitHub")
            print("  2. 在 Koyeb 控制台创建新服务")
            print("  3. 配置环境变量（参考 .env.production.example）")
            print("  4. 点击部署并等待构建完成\n")
        else:
            print("❌ 发现必须修复的问题，请先解决后再部署。\n")
            print("详细解决方案请参考: KOYEB_DEPLOYMENT_GUIDE.md\n")
        
        return is_ready
    
    def run_all_checks(self):
        """运行所有检查"""
        print("\n" + "🚀"*20)
        print("\n       Koyeb 部署前检查工具")
        print(f"       检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "🚀"*20 + "\n")
        
        results = {}
        
        results['required_vars'] = self.check_required_vars()
        self.check_optional_vars()
        results['database'] = self.test_database_connection()
        self.check_dependencies()
        self.check_compiler()
        self.check_config_files()
        
        is_ready = self.generate_report()
        
        # 保存报告到 JSON
        report = {
            'timestamp': datetime.now().isoformat(),
            'success_count': len(self.successes),
            'warning_count': len(self.warnings),
            'error_count': len(self.issues),
            'is_ready': is_ready,
            'successes': self.successes,
            'warnings': self.warnings,
            'issues': self.issues,
            'results': results
        }
        
        with open('deployment_check_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细报告已保存至: deployment_check_report.json\n")
        
        return is_ready


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Koyeb 部署前检查工具')
    parser.add_argument('--env', '-e', help='指定环境变量文件路径 (.env 格式)')
    parser.add_argument('--fix', '-f', action='store_true', help='尝试自动修复问题')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只输出结果')
    
    args = parser.parse_args()
    
    checker = DeploymentChecker(env_file=args.env)
    is_ready = checker.run_all_checks()
    
    sys.exit(0 if is_ready else 1)


if __name__ == '__main__':
    main()
