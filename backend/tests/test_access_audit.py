from fastapi.testclient import TestClient
from backend.app import main
from backend.app.api import access_audit
from backend.app.services.access_audit_service import AccessAuditService
from backend.app.services.auth_service import AuthService


def test_access_identity_permissions_and_sensitive_url_stripping(tmp_path,monkeypatch):
    auth=AuthService(tmp_path/'auth.sqlite3');auth.seed_demo_users(main.load_admin_users())
    audit=AccessAuditService(tmp_path/'audit.sqlite3')
    monkeypatch.setattr(main,'auth_service',auth)
    monkeypatch.setattr(access_audit,'access_service',audit)
    client=TestClient(main.app)
    visitor='abcdefghijklmnopqrstuv'
    assert client.post('/api/access/visit',json={'path':'/login?token=secret#private','visitor_id':visitor}).status_code==204
    response=client.post('/api/auth/login',json={'account':'teacher','password':'teacher123','role':'teacher'})
    assert response.status_code==200,response.text
    headers={'Authorization':'Bearer '+response.json()['token']}
    assert client.get('/api/admin/access-audit',headers=headers).status_code==403
    assert client.get('/api/admin/access-audit').status_code==401
    assert client.post('/api/access/visit',headers=headers,json={'path':'/teacher/dashboard','visitor_id':visitor}).status_code==204
    assert client.post('/api/access/visit',headers=headers,json={'path':'/teacher/dashboard','visitor_id':visitor,'account':'admin'}).status_code==422
    before=audit.list()['total']
    assert client.post('/api/access/visit',headers=headers,json={'path':'/teacher/dashboard','visitor_id':visitor,'kind':'heartbeat'}).status_code==204
    assert audit.list()['total']==before
    response=client.post('/api/auth/login',json={'account':'admin','password':'admin123','role':'admin'})
    admin={'Authorization':'Bearer '+response.json()['token']}
    result=client.get('/api/admin/access-audit',headers=admin).json()
    assert any(r['role']=='guest' and r['path']=='/login' for r in result['items'])
    assert any(r['account']=='teacher01' and r['kind']=='login' for r in result['items'])
    assert any(r['account']=='teacher01' and r['path']=='/teacher/dashboard' for r in result['items'])
    assert 'secret' not in str(result) and 'teacher123' not in str(result)
    assert result['online_sessions']==1 and result['online_accounts']==1
    assert client.get('/api/admin/access-audit?kind=page_view&size=1',headers=admin).json()['total']==2
    assert len(client.get('/api/admin/access-audit?kind=page_view&size=1&page=2',headers=admin).json()['items'])==1
    assert client.get('/api/admin/access-audit?size=1000',headers=admin).status_code==422
    filtered=client.get('/api/admin/access-audit?role=guest&kind=page_view&result=success',headers=admin).json()
    assert filtered['total']==1 and filtered['items'][0]['role']=='guest'
    assert client.get('/api/admin/access-audit?since=2999-01-01T00:00:00Z',headers=admin).json()['total']==0
    assert client.get('/api/admin/access-audit?since=2026-11-14T00:00:00Z&until=2026-11-13T00:00:00Z',headers=admin).status_code==422
    monkeypatch.setattr(main,'read_json',lambda name:[{'data_source':'教材'},{'data_source':'教材'},{'data_source':'病例'}])
    sources=client.get('/api/admin/knowledge-status',headers=admin).json()
    assert sources['source_counts']=={'教材':2,'病例':1}
    assert sum(sources['source_counts'].values())==sources['items']==3


def test_persistence_and_anonymous_forwarded_ip_not_trusted(tmp_path,monkeypatch):
    audit=AccessAuditService(tmp_path/'audit.sqlite3');monkeypatch.setattr(access_audit,'access_service',audit)
    client=TestClient(main.app)
    assert client.post('/api/access/visit',headers={'X-Forwarded-For':'8.8.8.8'},json={'path':'/landing','visitor_id':'0123456789abcdef'}).status_code==204
    persisted=AccessAuditService(tmp_path/'audit.sqlite3').list()
    assert persisted['items'][0]['ip']=='testclient'
    assert persisted['items'][0]['role']=='guest'
