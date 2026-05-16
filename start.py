import sys
import os

print("=" * 50)
print("码上开悟 - C++学习平台 启动脚本")
print("=" * 50)
print()

print("[1/5] 检查依赖...")
try:
    import flask
    print(f"    Flask {flask.__version__} ✓")
except ImportError as e:
    print(f"    ✗ 缺少 Flask: {e}")
    print("    请运行: pip install Flask")
    sys.exit(1)

try:
    import flask_login
    print(f"    Flask-Login ✓")
except ImportError:
    print(f"    ✗ 缺少 Flask-Login")
    sys.exit(1)

try:
    import flask_caching
    print(f"    Flask-Caching ✓")
except ImportError:
    print(f"    ✗ 缺少 Flask-Caching")
    sys.exit(1)

try:
    import flask_limiter
    print(f"    Flask-Limiter ✓")
except ImportError:
    print(f"    ✗ 缺少 Flask-Limiter")
    sys.exit(1)

print()
print("[2/5] 加载配置...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("    .env 加载完成")
    db_type = os.getenv('DB_TYPE', 'sqlite')
    print(f"    数据库类型: {db_type}")
except Exception as e:
    print(f"    ✗ 配置加载失败: {e}")
    sys.exit(1)

print()
print("[3/5] 初始化数据库...")
try:
    from app import create_app
    print("    应用工厂初始化中...")
    app = create_app()
    print("    ✓ 数据库连接成功")
except Exception as e:
    print(f"    ✗ 数据库初始化失败: {e}")
    print()
    print("    可能原因:")
    print("    - MySQL 服务未启动 (请检查 MySQL 服务)")
    print("    - 数据库 learning_platform 不存在 (请先创建)")
    print("    - .env 配置的数据库信息有误")
    print()
    print("    解决方案:")
    print("    1. 确保 MySQL 服务运行中")
    print("    2. 创建数据库: CREATE DATABASE learning_platform;")
    print("    3. 修改 .env 中的数据库配置")
    print("    4. 或者将 .env 中 DB_TYPE 改为 sqlite (无需配置)")
    sys.exit(1)

print()
print("[4/5] 检查 AI 服务...")
ollama_url = os.getenv('OLLAMA_BASE_URL', '')
minimax_key = os.getenv('MINIMAX_API_KEY', '')
if ollama_url:
    print(f"    Ollama: {ollama_url}")
try:
    from app.services.provider_manager import ProviderManager
    pm = ProviderManager.get_instance()
    model_info = pm.get_current_model_info()
    print(f"    当前模型: {model_info.get('name', 'unknown')}")
    print(f"    模型类型: {model_info.get('type', 'unknown')}")
    if model_info.get('is_healthy'):
        print("    状态: ✓ 正常")
    else:
        print("    状态: ⚠ 可能不可用（不影响基本功能）")
except Exception as e:
    print(f"    AI 服务检查跳过: {e}")

print()
print("[5/5] 启动服务器...")
print("    地址: http://localhost:5001")
print("    调试模式: 已启用")
print()
print("=" * 50)
print("按 Ctrl+C 停止服务器")
print("=" * 50)
print()

try:
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=True)
except KeyboardInterrupt:
    print()
    print("服务器已停止")
except Exception as e:
    print()
    print(f"✗ 服务器启动失败: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...")