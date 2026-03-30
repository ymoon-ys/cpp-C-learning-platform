# Koyeb 环境变量配置指南

## 📋 环境变量清单

### 数据库配置
| 环境变量 | 值 | 说明 |
|---------|-----|------|
| DB_TYPE | mysql | 数据库类型（固定值） |
| MYSQL_HOST | mysql-3c6bff41-project-4c37.j.aivencloud.com | Aiven MySQL 主机地址 |
| MYSQL_PORT | 12581 | Aiven MySQL 端口 |
| MYSQL_USER | avnadmin | 数据库用户名 |
| MYSQL_PASSWORD | [Aiven MySQL 密码] | 数据库密码 |
| MYSQL_DATABASE | defaultdb | 数据库名称 |

### 其他配置
| 环境变量 | 值 | 说明 |
|---------|-----|------|
| BAIDU_OCR_API_KEY | WW3rGrh26YGKEX3j2JKLE31r | 百度 OCR API Key |
| BAIDU_OCR_SECRET_KEY | 1tDEpjnZRYTA2ldVjgMO0piRCJHOkO2D | 百度 OCR Secret Key |

## 🔧 如何在 Koyeb 中配置

1. **登录 Koyeb 控制台**
   - 访问 https://app.koyeb.com/
   - 进入你的服务页面

2. **配置环境变量**
   - 点击左侧菜单的 **Settings**
   - 选择 **Environment Variables** 选项卡
   - 点击 **Add Variable** 按钮
   - 按照上面的表格逐个添加环境变量

3. **重启服务**
   - 点击 **Restart** 按钮重启服务
   - 等待部署完成

## 🔍 查看部署日志

1. 进入服务页面
2. 点击 **Deployments** 选项卡
3. 选择最新的部署
4. 查看 **Logs** 部分，确认：
   - 数据库连接成功
   - 服务启动正常

## 📝 注意事项

1. **数据导入**：
   - 由于 Aiven 限制外部 IP 访问，无法直接从本地导入数据
   - 应用启动时会自动创建必要的数据库表结构
   - 你可以通过注册新用户来测试系统

2. **数据库连接**：
   - 确保所有环境变量都正确设置
   - 检查 Koyeb 部署日志中的连接信息
   - 如果出现连接错误，检查 Aiven 控制台的网络配置

3. **服务状态**：
   - 部署完成后，服务状态应该显示为 **Healthy**
   - 访问应用 URL 确认服务正常运行

## 🚀 访问应用

部署成功后，你可以通过以下 URL 访问应用：
**https://real-kettle-ymoon-df35652.koyeb.app**
