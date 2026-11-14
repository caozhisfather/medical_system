from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import re
import sqlite3
import pytest
from backend.app.services.auth_service import AuthService
from backend.app.services.mail_service import MailService

@pytest.fixture
def service(tmp_path):
    return AuthService(tmp_path/'auth.sqlite3')

def test_code_scope_attempt_limit_and_storage(service):
    user, code=service.register('codes','Code Student','code@example.com','Medical123','student')
    assert re.fullmatch('[0-9]{6}',code)
    with sqlite3.connect(service.database_path) as db:
        stored=db.execute('SELECT code_hash FROM email_verification_codes').fetchone()[0]
    assert stored!=code and code not in stored
    with pytest.raises(ValueError):service.verify_email_code('other@example.com',code)
    wrong='000001' if code!='000001' else '000002'
    for _ in range(5):
        with pytest.raises(ValueError):service.verify_email_code(user['email'],wrong)
    with pytest.raises(ValueError,match='次数'):service.verify_email_code(user['email'],code)
    with service._connection() as db:
        assert db.execute('SELECT attempts FROM email_verification_codes').fetchone()[0]==5

def test_resend_cooldown_invalidation_expiry_and_hourly_limit(service):
    now=datetime.now(timezone.utc)
    with patch('backend.app.services.auth_service._now',return_value=now):
        _,old=service.register('resend','Resend Student','resend@example.com','Medical123','student')
        with pytest.raises(ValueError,match='60秒'):service.create_verification('resend@example.com')
    with patch('backend.app.services.auth_service._now',return_value=now+timedelta(seconds=61)):
        _,new=service.create_verification('resend@example.com')
        with pytest.raises(ValueError):service.verify_email_code('resend@example.com',old)
    with patch('backend.app.services.auth_service._now',return_value=now+timedelta(minutes=12)):
        with pytest.raises(ValueError,match='过期'):service.verify_email_code('resend@example.com',new)
        for _ in range(3):
            service.verification_delivery_failed('resend@example.com',new)
            _,new=service.create_verification('resend@example.com')
        with pytest.raises(ValueError,match='频繁'):service.create_verification('resend@example.com')

def test_leading_zero_and_existing_database_safe_upgrade(service):
    with patch('backend.app.services.auth_service.secrets.randbelow',return_value=42):
        user,code=service.register('zeros','Zero Student','zero@example.com','Medical123','student')
    assert code=='000042'
    upgraded=AuthService(service.database_path)
    assert upgraded.verify_email_code(user['email'],code)['status']=='active'
    with pytest.raises(ValueError):upgraded.verify_email_code(user['email'],code)

def test_mail_contains_code_no_verification_link(monkeypatch):
    sent={}
    service=MailService('smtp.163.com',465,'sender@example.com','not-a-real-secret','AI Medical','http://172.16.7.120')
    monkeypatch.setattr(service,'_send',lambda recipient,subject,text,html:sent.update(recipient=recipient,text=text,html=html))
    service.send_verification('recipient@example.com','000042')
    assert '000042' in sent['text'] and '000042' in sent['html']
    assert '/verify-email?token=' not in sent['html']
    with pytest.raises(ValueError):service.send_verification('recipient@example.com','not-code')

def test_legacy_database_upgrade_preserves_users_and_sessions(service):
    user,code=service.register('migration','Migration Student','migration@example.com','Medical123','student')
    service.verify_email_code(user['email'],code)
    token,_=service.login('migration','Medical123','student')
    with service._connection() as db:
        db.execute('DROP TABLE email_verification_codes')
    upgraded=AuthService(service.database_path)
    assert upgraded.authenticated_user(token)['id']==user['id']
    assert upgraded.login('migration','Medical123','student')[1]['id']==user['id']

def test_concurrent_verification_is_single_use(service):
    from concurrent.futures import ThreadPoolExecutor
    user,code=service.register('concurrent','Concurrent Student','concurrent@example.com','Medical123','student')
    def verify():
        try:return service.verify_email_code(user['email'],code)['status']=='active'
        except ValueError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _:verify(),range(2)))==1
