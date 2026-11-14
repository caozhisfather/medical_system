from __future__ import annotations

import smtplib
from email.message import EmailMessage


class MailService:
    def __init__(self, host: str, port: int, username: str, password: str, sender_name: str, frontend_url: str) -> None:
        self.host, self.port = host, port
        self.username, self.password = username, password
        self.sender_name, self.frontend_url = sender_name, frontend_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.host and self.username and self.password)

    def _send(self, recipient: str, subject: str, text: str, html: str) -> None:
        if not self.configured:
            raise RuntimeError("邮件服务尚未配置，请在 env/.env 中填写 SMTP 授权码")
        message = EmailMessage()
        message["From"] = f"{self.sender_name} <{self.username}>"
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as server:
            server.login(self.username, self.password)
            server.send_message(message)

    def send_verification(self, recipient: str, code: str) -> None:
        if len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ValueError("Invalid verification code")
        self._send(recipient, "AI Medical 邮箱验证码", f"你的邮箱验证码是：{code}。10分钟内有效，请勿向他人透露。重新发送后旧验证码失效。如非本人操作，请忽略。",
            f"""<html><body style="background:#f1f6ff;font-family:Arial,sans-serif;color:#102a56"><div style="max-width:520px;margin:32px auto;padding:32px;background:white;border-radius:18px"><strong style="color:#155eef">AI Medical</strong><h1 style="font-size:24px">验证你的邮箱</h1><p>请在网站输入以下六位验证码：</p><div style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#155eef;padding:20px;background:#edf5ff;text-align:center">{code}</div><p>10分钟内有效。重新发送后旧验证码失效。</p><p>请勿向他人透露验证码。如非本人操作，请忽略此邮件。</p></div></body></html>""")

    def send_password_reset(self, recipient: str, token: str) -> None:
        link = f"{self.frontend_url}/reset-password?token={token}"
        self._send(recipient, "重置你的芯聆知医密码", f"请在15分钟内打开链接重置密码：{link}", self._template("重置密码", "该链接将在15分钟后失效且只能使用一次。", link, "重置密码"))

    def _template(self, title: str, description: str, link: str, action: str) -> str:
        return f"""<!doctype html><html><body style="margin:0;background:#edf3f2;font-family:Arial,sans-serif;color:#173b3f">
        <div style="max-width:560px;margin:32px auto;background:#fff;border-radius:8px;padding:36px">
        <div style="color:#0f766e;font-size:14px;font-weight:bold">芯聆知医</div><h1 style="font-size:24px">{title}</h1>
        <p style="line-height:1.7;color:#587276">{description}</p><a href="{link}" style="display:inline-block;padding:13px 22px;background:#0f766e;color:#fff;text-decoration:none;border-radius:6px;font-weight:bold">{action}</a>
        <p style="margin-top:28px;font-size:12px;color:#809396">如果不是你本人操作，请忽略此邮件。</p></div></body></html>"""
