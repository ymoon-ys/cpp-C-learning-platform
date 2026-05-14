# C-Learning-Platform UI 优化完整脚本
# 用于恢复被还原的UI优化效果
# 使用方法: 右键 -> 使用 PowerShell 运行

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  C-Learning-Platform UI 优化完整脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

Write-Host "[1/12] 更新 _variables.scss 完整配置..." -ForegroundColor Yellow
$variablesContent = @"
// ============================================
// 设计令牌 (Design Tokens) - 变量定义
// C++学习平台 SCSS设计系统核心配置
// ============================================

// Primary Colors
`$primary-color: #6C5CE7;
`$primary-light: #A29BFE;
`$primary-dark: #5A4BD1;
`$secondary-color: #7C3AED;
`$accent-color: #F59E0B;
`$accent-light: #FBBF24;

// 功能色
`$success-color: #10B981;
`$warning-color: #F59E0B;
`$danger-color: #EF4444;
`$info-color: #3B82F6;

// 文字颜色
`$text-primary: #1E293B;
`$text-secondary: #64748B;
`$text-muted: #94A3B8;
`$text-white: #ffffff;

// 渐变色
`$primary-gradient: linear-gradient(135deg, #6C5CE7 0%, #7C3AED 50%, #A855F7 100%);
`$secondary-gradient: linear-gradient(180deg, #6C5CE7 0%, #7C3AED 100%);
`$accent-gradient: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
`$success-gradient: linear-gradient(135deg, #10B981 0%, #34D399 100%);
`$warning-gradient: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
`$danger-gradient: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
`$info-gradient: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);

// 背景色
`$bg-light: #F8FAFC;
`$bg-white: #ffffff;
`$bg-dark: #0F172A;
`$bg-gradient: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 50%, #DDD6FE 100%);
`$bg-warm: #FFFBEB;

// 边框色
`$border-color: #E2E8F0;
`$border-light: #F1F5F9;
`$border-focus: `$primary-color;

// 间距系统
`$spacing-unit: 4px;
`$spacing-xs: `$spacing-unit;
`$spacing-sm: `$spacing-unit * 2;
`$spacing-md: `$spacing-unit * 3;
`$spacing-lg: `$spacing-unit * 4;
`$spacing-xl: `$spacing-unit * 6;
`$spacing-2xl: `$spacing-unit * 8;
`$spacing-3xl: `$spacing-unit * 12;

// 阴影系统
`$shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
`$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
`$shadow-lg: 0 10px 25px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
`$shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
`$shadow-inner: inset 0 2px 4px rgba(0, 0, 0, 0.04);
`$shadow-primary: 0 4px 14px rgba(108, 92, 231, 0.25);
`$shadow-accent: 0 4px 14px rgba(245, 158, 11, 0.25);

// 圆角系统
`$radius-sm: 8px;
`$radius-md: 12px;
`$radius-lg: 16px;
`$radius-xl: 20px;
`$radius-full: 50%;
`$radius-none: 0;

// 响应式断点
`$breakpoints: (
  'xs': 0,
  'sm': 576px,
  'md': 768px,
  'lg': 992px,
  'xl': 1200px,
  'xxl': 1400px
);

// 字体系统
`$font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                   'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei',
                   sans-serif;
`$font-family-mono: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
`$font-size-base: 16px;
`$line-height-base: 1.6;
`$font-size-xs: 12px;
`$font-size-sm: 14px;
`$font-size-md: 16px;
`$font-size-lg: 18px;
`$font-size-xl: 20px;
`$font-size-2xl: 24px;
`$font-size-3xl: 30px;
`$font-size-4xl: 36px;
`$font-weight-light: 300;
`$font-weight-normal: 400;
`$font-weight-medium: 500;
`$font-weight-semibold: 600;
`$font-weight-bold: 700;

// 过渡动画
`$transition-fast: 150ms ease-in-out;
`$transition-base: 250ms ease-in-out;
`$transition-slow: 350ms ease-in-out;

// Z-index
`$z-dropdown: 100;
`$z-sticky: 200;
`$z-fixed: 300;
`$z-modal-backdrop: 400;
`$z-modal: 500;
`$z-popover: 600;
`$z-tooltip: 700;
`$z-toast: 800;

// 容器宽度
`$container-sm: 540px;
`$container-md: 720px;
`$container-lg: 960px;
`$container-xl: 1140px;
`$container-xxl: 1320px;
"@
Set-Content "static\src\scss\_variables.scss" -Value $variablesContent -Encoding UTF8
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[2/12] 修复 _base.scss 废弃函数..." -ForegroundColor Yellow
$baseFile = "static\src\scss\_base.scss"
if (Test-Path $baseFile) {
    $content = Get-Content $baseFile -Encoding UTF8
    $content = $content -replace 'darken\(\$primary-color, 10%\)', '$primary-dark'
    Set-Content $baseFile -Value $content -Encoding UTF8
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[3/12] 修复 _loading.scss 废弃函数..." -ForegroundColor Yellow
$loadingFile = "static\src\scss\components\_loading.scss"
if (Test-Path $loadingFile) {
    $content = Get-Content $loadingFile -Encoding UTF8
    $content = $content -replace 'darken\(\$bg-light, 3%\) 37%', '#EEF2F7 37%'
    Set-Content $loadingFile -Value $content -Encoding UTF8
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[4/12] 修复 _cards.scss 颜色..." -ForegroundColor Yellow
$cardsFile = "static\src\scss\components\_cards.scss"
if (Test-Path $cardsFile) {
    $content = Get-Content $cardsFile -Encoding UTF8
    $content = $content -replace 'color: darken\(\$warning-color, 10%\)', 'color: #B45309'
    Set-Content $cardsFile -Value $content -Encoding UTF8
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[5/12] 更新 HTML 模板颜色..." -ForegroundColor Yellow
Get-ChildItem "app\templates" -Recurse -Filter "*.html" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -Encoding UTF8
    $content = $content -replace '#667eea', '#6C5CE7'
    $content = $content -replace '#764ba2', '#7C3AED'
    $content = $content -replace '#2c3e50', '#1E293B'
    $content = $content -replace '#7f8c8d', '#64748B'
    $content = $content -replace '#95a5a6', '#94A3B8'
    $content = $content -replace '#00b894', '#10B981'
    $content = $content -replace '#00cec9', '#34D399'
    $content = $content -replace '#fd9644', '#F59E0B'
    $content = $content -replace '#fc8c0c', '#FBBF24'
    $content = $content -replace '#a55eea', '#8B5CF6'
    $content = $content -replace '#8854d0', '#7C3AED'
    $content = $content -replace '#e0e0e0', '#E2E8F0'
    $content = $content -replace '#f0f0f0', '#F1F5F9'
    $content = $content -replace '#f8f9fa', '#F8FAFC'
    $content = $content -replace '#d0d0d0', '#CBD5E1'
    $content = $content -replace '#bdc3c7', '#94A3B8'
    $content = $content -replace 'rgba\(102, 126, 234', 'rgba(108, 92, 231'
    Set-Content $_.FullName -Value $content -NoNewline -Encoding UTF8
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[6/12] 更新静态CSS文件..." -ForegroundColor Yellow
foreach ($cssFile in @("static\style.css", "static\modern-design.css")) {
    if (Test-Path $cssFile) {
        $content = Get-Content $cssFile -Raw -Encoding UTF8
        $content = $content -replace '#667eea', '#6C5CE7'
        $content = $content -replace '#764ba2', '#7C3AED'
        $content = $content -replace '#2c3e50', '#1E293B'
        $content = $content -replace '#7f8c8d', '#64748B'
        $content = $content -replace '#95a5a6', '#94A3B8'
        $content = $content -replace '#00b894', '#10B981'
        $content = $content -replace '#00cec9', '#34D399'
        $content = $content -replace '#fd9644', '#F59E0B'
        $content = $content -replace '#fc8c0c', '#FBBF24'
        $content = $content -replace '#a55eea', '#8B5CF6'
        $content = $content -replace '#8854d0', '#7C3AED'
        $content = $content -replace '#e0e0e0', '#E2E8F0'
        $content = $content -replace '#f0f0f0', '#F1F5F9'
        $content = $content -replace '#f8f9fa', '#F8FAFC'
        $content = $content -replace '#d0d0d0', '#CBD5E1'
        $content = $content -replace '#bdc3c7', '#94A3B8'
        $content = $content -replace 'rgba\(102, 126, 234', 'rgba(108, 92, 231'
        Set-Content $cssFile -Value $content -NoNewline -Encoding UTF8
        Write-Host "  - $cssFile" -ForegroundColor Gray
    }
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[7/12] 更新 base.html 主题色..." -ForegroundColor Yellow
$baseHtml = "app\templates\base.html"
if (Test-Path $baseHtml) {
    $content = Get-Content $baseHtml -Encoding UTF8
    $content = $content -replace '#667eea', '#6C5CE7'
    $content = $content -replace '#667eea 0%, #764ba2 100%', '#F59E0B 0%, #FBBF24 100%'
    Set-Content $baseHtml -Value $content -Encoding UTF8
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[8/12] 更新 student/dashboard.html..." -ForegroundColor Yellow
$dashHtml = "app\templates\student\dashboard.html"
if (Test-Path $dashHtml) {
    $content = Get-Content $dashHtml -Raw -Encoding UTF8
    $content = $content -replace '#667eea', '#6C5CE7'
    $content = $content -replace '#764ba2', '#7C3AED'
    Set-Content $dashHtml -Value $content -NoNewline -Encoding UTF8
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[9/12] 验证旧颜色是否还存在..." -ForegroundColor Yellow
$oldColorCount = 0
$files = Get-ChildItem "app\templates" -Recurse -Filter "*.html" -ErrorAction SilentlyContinue
foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match '#667eea|#764ba2') {
        $oldColorCount++
        Write-Host "  发现旧颜色: $($file.Name)" -ForegroundColor Red
    }
}
if ($oldColorCount -eq 0) {
    Write-Host "  没有发现旧颜色!" -ForegroundColor Green
}

Write-Host "[10/12] 更新 SCSS 组件文件..." -ForegroundColor Yellow
$scssFiles = @(
    "static\src\scss\components\_sidebar.scss",
    "static\src\scss\components\_cards.scss",
    "static\src\scss\components\_dashboard.scss",
    "static\src\scss\components\_auth.scss",
    "static\src\scss\components\_forms.scss",
    "static\src\scss\components\_toast.scss",
    "static\src\scss\components\_community.scss",
    "static\src\scss\components\_ai-assistant.scss"
)
foreach ($scssFile in $scssFiles) {
    if (Test-Path $scssFile) {
        $content = Get-Content $scssFile -Raw -Encoding UTF8
        $content = $content -replace '#667eea', '#6C5CE7'
        $content = $content -replace '#764ba2', '#7C3AED'
        $content = $content -replace '#2c3e50', '#1E293B'
        $content = $content -replace '#7f8c8d', '#64748B'
        $content = $content -replace '#95a5a6', '#94A3B8'
        Set-Content $scssFile -Value $content -NoNewline -Encoding UTF8
    }
}
Write-Host "  完成!" -ForegroundColor Green

Write-Host "[11/12] 构建项目..." -ForegroundColor Yellow
npm run build 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  构建成功!" -ForegroundColor Green
} else {
    Write-Host "  构建失败!" -ForegroundColor Red
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  UI 优化完成! (耗时: $($duration.ToString('0.0'))秒)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 下次代码被还原后，再次运行此脚本即可恢复优化" -ForegroundColor Yellow
Write-Host "运行 'npm run dev' 启动开发服务器" -ForegroundColor Yellow
Write-Host ""