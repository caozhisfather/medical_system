# 邮箱认证配置

当前账号系统使用 SQLite 保存用户和服务端会话，支持学生/教师注册、邮箱验证、登录退出、密码找回与教师账号审核。认证数据库默认位于 `data/auth.sqlite3`，已加入 `.gitignore`。

## 1. 创建本地配置

后端读取 `env/.env`。在项目根目录执行：

```powershell
New-Item -ItemType Directory -Force env
Copy-Item .env.example env/.env
```

## 2. 配置 SMTP

在邮箱服务商后台开启 SMTP，创建独立的客户端授权码，然后填写：

```dotenv
MAIL_HOST=smtp.163.com
MAIL_PORT=465
MAIL_USERNAME=your-account@example.com
MAIL_PASSWORD=your-smtp-authorization-code
MAIL_FROM_NAME=临思智训
PUBLIC_FRONTEND_URL=http://127.0.0.1:5173
```

当前实现使用 SMTP SSL，端口通常为 `465`。其他邮箱服务商请使用其提供的 SSL 主机和端口。`PUBLIC_FRONTEND_URL` 必须是用户可以访问的前端地址，邮件中的验证和重置链接会基于它生成。

不要填写邮箱网页登录密码，不要提交 `env/.env`、SMTP 授权码或 `data/auth.sqlite3`。若授权码曾出现在聊天记录、压缩包、日志或 Git 历史中，应立即在邮箱服务商后台撤销并重新生成。

## 3. 账号流程

- 学生：注册 -> 邮箱验证 -> 直接登录。
- 教师：注册 -> 邮箱验证 -> 管理员在用户审核区批准 -> 登录。
- 忘记密码：申请重置邮件 -> 15 分钟内设置新密码；成功后旧登录会话全部失效。
- 验证链接：30 分钟有效、仅可使用一次；每个账号每小时最多创建 5 个同用途令牌。

内置演示账号不需要邮箱验证。正式部署时应删除或禁用演示账号，并将 SQLite 方案替换为具备备份、审计、速率限制和高可用能力的正式身份服务。

## 4. 验证配置

启动后端并访问 `GET /api/health`。当 `auth.mail_configured` 为 `true` 时，SMTP 用户名和授权码已被读取。随后使用测试邮箱完成一次注册、验证、登录、找回密码流程，并确认邮件链接指向正确的前端域名。
