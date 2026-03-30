"""
MySQL 状态检查脚本 (使用绝对路径)
"""
import os
import sys
import subprocess

def get_mysql_path():
    """获取MySQL安装路径"""
    possible_paths = [
        "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
        "C:\\Program Files (x86)\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
        "C:\\xampp\\mysql\\bin\\mysql.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def check_mysql_installed():
    """检查MySQL是否安装"""
    mysql_path = get_mysql_path()
    if mysql_path:
        print(f'✅ MySQL已安装: {mysql_path}')
        return mysql_path
    else:
        print('❌ MySQL未安装')
        return None

def check_mysql_service():
    """检查MySQL服务状态"""
    try:
        result = subprocess.run(['net', 'start'], capture_output=True, text=True)
        if 'mysql' in result.stdout.lower():
            print('✅ MySQL服务正在运行')
            return True
        else:
            print('⚠️  MySQL服务未运行')
            return False
    except Exception as e:
        print(f'❌ 检查服务失败: {e}')
        return False

def test_mysql_connection(mysql_path, host='localhost', user='root', password='123456', database='learning_platform'):
    """测试MySQL连接"""
    try:
        # 测试基本连接
        cmd = [mysql_path, '-h', host, '-u', user, f'-p{password}', '-e', 'SELECT 1']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f'✅ MySQL连接成功')
            
            # 测试数据库
            cmd = [mysql_path, '-h', host, '-u', user, f'-p{password}', '-e', f'CREATE DATABASE IF NOT EXISTS {database}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f'✅ 数据库 {database} 准备就绪')
                return True
            else:
                print(f'⚠️ 创建数据库失败: {result.stderr}')
                return False
        else:
            print(f'❌ MySQL连接失败: {result.stderr}')
            return False
    except subprocess.TimeoutExpired:
        print('❌ 连接超时')
        return False
    except Exception as e:
        print(f'❌ 连接失败: {e}')
        return False

def main():
    print('\n=== MySQL 状态检查 ===\n')
    
    print('1. 检查MySQL安装...')
    mysql_path = check_mysql_installed()
    print()
    
    if mysql_path:
        print('2. 检查MySQL服务...')
        service_running = check_mysql_service()
        print()
        
        print('3. 测试MySQL连接...')
        connected = test_mysql_connection(mysql_path)
        print()
        
        if service_running and connected:
            print('✅ MySQL配置正常，可以开始迁移数据')
            print('\n运行以下命令迁移数据:')
            print('  python migrate_to_mysql.py')
        else:
            print('⚠️  MySQL配置有问题，请检查:')
            if not service_running:
                print('  - 启动MySQL服务')
                print('  - 或使用MySQL Installer管理服务')
            if not connected:
                print('  - 检查MySQL密码是否正确')
                print('  - 确保MySQL服务正在运行')
    else:
        print('\n=== MySQL 安装指南 ===\n')
        print('MySQL已安装但未找到可执行文件')
        print('请检查MySQL安装目录和权限')
    
    print()

if __name__ == '__main__':
    main()
