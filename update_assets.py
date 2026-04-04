#!/usr/bin/env python3
"""
构建后脚本：自动更新base.html中的静态资源引用
在Vite构建后运行，将生成的文件名同步到模板中
"""
import os
import re
import glob
from pathlib import Path

def update_base_html():
    base_dir = Path(__file__).parent
    dist_assets = base_dir / 'static' / 'dist' / 'assets'
    template_file = base_dir / 'app' / 'templates' / 'base.html'
    
    if not dist_assets.exists():
        print(f'[ERR] Distribution directory not found: {dist_assets}')
        return False
    
    # 查找CSS和JS文件
    css_files = list(dist_assets.glob('main*.css'))
    js_files = list(dist_assets.glob('main*.js'))
    
    if not css_files:
        print('[WARN] No CSS files found in dist/assets')
        return False
    
    if not js_files:
        print('[WARN] No JS files found in dist/assets')
        return False
    
    css_file = css_files[0].name  # 取第一个匹配的CSS文件
    js_file = js_files[0].name   # 取第一个匹配的JS文件
    
    print(f'[OK] Found CSS file: {css_file}')
    print(f'[OK] Found JS file: {js_file}')
    
    # 读取模板文件
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新CSS引用
    content = re.sub(
        r"filename='dist/assets/[^']*\.css'",
        f"filename='dist/assets/{css_file}'",
        content
    )
    
    # 更新JS引用
    content = re.sub(
        r"filename='dist/assets/[^']*\.js'",
        f"filename='dist/assets/{js_file}'",
        content
    )
    
    # 写回模板文件
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'[OK] Updated {template_file} with new asset references')
    return True

if __name__ == '__main__':
    success = update_base_html()
    exit(0 if success else 1)