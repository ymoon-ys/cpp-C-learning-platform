#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 数据库连接测试脚本
========================

用于验证 .env 中的数据库配置是否正确
"""

import os
from dotenv import load_dotenv
import mysql.connector

def test_database_connection():
    """测试 MySQL 连接"""
    
    # 加载环境变量
    load_dotenv()
    
    print("\n" + "="*60)
    print("  🗄️  MySQL 数据库连接测试")
    print("="*60 + "\n")
    
    # 获取配置
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = int(os.getenv('MYSQL_PORT', '3306'))
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', '')
    
    # 显示配置信息（隐藏密码）
    print(f"📋 连接配置:")
    print(f"   主机: {host}")
    print(f"   端口: {port}")
    print(f"   用户: {user}")
    print(f"   密码: {'*' * len(password) if password else '(空)'}")
    print(f"   数据库: {database}\n")
    
    # 检查必需配置
    if not all([host, user, password, database]):
        print("❌ 错误：缺少必需的数据库配置！")
        print("请检查 .env 文件中的 MYSQL_* 配置项\n")
        return False
    
    # 尝试连接
    try:
        print("⏳ 正在连接数据库...")
        
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10,
            autocommit=True
        )
        
        print("✅ 数据库连接成功！\n")
        
        # 获取 MySQL 版本
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"📌 MySQL 版本: {version}")
        
        # 检查数据库是否存在并获取信息
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]
        print(f"📌 当前数据库: {current_db}")
        
        # 获取表列表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📊 数据库中的表 ({len(tables)} 个):")
            for i, (table_name,) in enumerate(tables, 1):
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                print(f"   {i}. {table_name} ({count} 条记录)")
        else:
            print("\n📊 数据库为空（没有表）")
            print("   应用启动时会自动创建所需的表\n")
        
        # 测试基本操作权限
        print("\n🔐 权限测试:")
        tests = [
            ("CREATE TABLE", "CREATE TABLE IF NOT EXISTS _test_perm (id INT)"),
            ("INSERT", "INSERT INTO _test_perm (id) VALUES (1)"),
            ("SELECT", "SELECT * FROM _test_perm"),
            ("UPDATE", "UPDATE _test_perm SET id = 2 WHERE id = 1"),
            ("DELETE", "DELETE FROM _test_perm WHERE id = 2"),
            ("DROP TABLE", "DROP TABLE IF EXISTS _test_perm")
        ]
        
        for test_name, sql in tests:
            try:
                cursor.execute(sql)
                print(f"   ✅ {test_name}: 成功")
            except Exception as e:
                print(f"   ❌ {test_name}: 失败 - {str(e)}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("  ✅ 所有测试通过！数据库配置正确")
        print("="*60 + "\n")
        
        return True
        
    except mysql.connector.Error as err:
        error_type = type(err).__name__
        error_msg = str(err)
        
        print(f"\n❌ 数据库连接失败!")
        print(f"   错误类型: {error_type}")
        print(f"   错误信息: {error_msg}\n")
        
        # 提供解决方案建议
        print("💡 可能的原因和解决方案:\n")
        
        if "Access denied" in error_msg or "1045" in error_msg:
            print("   ❌ 用户名或密码错误")
            print("      解决：检查 .env 中的 MYSQL_USER 和 MYSQL_PASSWORD\n")
            
        elif "Unknown database" in error_msg or "1049" in error_msg:
            print("   ❌ 数据库不存在")
            print(f"      解决：创建数据库 '{database}'")
            print(f"      命令: CREATE DATABASE {database} CHARACTER SET utf8mb4;\n")
            
        elif "Can't connect" in error_msg or "2003" in error_msg or "2002" in error_msg:
            print("   ❌ 无法连接到 MySQL 服务器")
            print("      可能原因:")
            print("      1. MySQL 服务未启动")
            print("      2. 主机地址或端口不正确")
            print("      3. 防火墙阻止了连接\n")
            
        elif "Authentication plugin" in error_msg:
            print("   ❌ 认证插件不兼容")
            print("      解决：修改用户认证方式为 mysql_native_password")
            print(f"      命令: ALTER USER '{user}'@'localhost' IDENTIFIED WITH mysql_native_password BY '{password}';\n")
            
        else:
            print("   ❌ 其他错误")
            print("      请检查 MySQL 服务器状态和配置\n")
        
        print("="*60)
        return False
        
    except Exception as e:
        print(f"\n❌ 发生未知错误: {type(e).__name__}: {e}\n")
        return False


if __name__ == '__main__':
    import sys
    success = test_database_connection()
    sys.exit(0 if success else 1)
