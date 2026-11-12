"""Workflow regression tests use disposable databases, never project data."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import io
import sqlite3

import pytest
from fastapi.testclient import TestClient
from backend.app import main
from backend.app.services.auth_service import AuthService
from backend.app.services.classroom_service import ClassroomService
from backend.app.services.anatomy_learning_service import AnatomyLearningService
from backend.app.api.teaching import build_service


@pytest.fixture
def env(tmp_path, monkeypatch):
    auth = AuthService(tmp_path/'auth.sqlite3')
    auth.seed_demo_users(main.load_admin_users())
    monkeypatch.setattr(main,'auth_service',auth)
    monkeypatch.setattr(main,'classroom_service',ClassroomService(tmp_path/'classes.sqlite3'))
    monkeypatch.setattr(main,'anatomy_learning_service',AnatomyLearningService(tmp_path/'learning.sqlite3'))
    monkeypatch.setattr(main,'write_audit_log',lambda *a,**kw:None)
    client = TestClient(main.app)
    def login(account,password,role):
        r=client.post('/api/auth/login',json=dict(account=account,password=password,role=role))
        assert r.status_code==200,r.text
        return {'Authorization':'Bearer '+r.json()['token']}
    t=login('teacher','teacher123','teacher'); st=login('student','student123','student')
    return client,t,st,tmp_path


def ok(response, code=200):
    assert response.status_code==code,response.text
    return response.json()


def create(c,t,name='解剖学教学班'):
    return ok(c.post('/api/teaching/classes',headers=t,json={'name':name,'major':'临床医学','grade':'2026','semester':'秋季'}))


def test_full_teaching_workflow(env):
    c,t,st,root=env
    m=ok(c.get('/api/teaching/metrics',headers=t))
    assert m=={'classes':0,'students':0,'attendance_rate':None,'assignment_rate':None,'progress':None}
    cl=create(c,t); cid=cl['id']; p='/api/teaching/classes/'+cid
    ok(c.post('/api/classrooms/join',headers=st,json={'code':cl['code']}))
    w=ok(c.get(p+'/workspace',headers=t)); sid=w['students'][0]['student_id']
    assert ok(c.get('/api/teaching/metrics',headers=t))['students']==1
    assert w['overview'] is None and not w['analytics']['has_activity']
    attendance={'title':'课堂考勤','attendance_date':datetime.now(timezone(timedelta(hours=8))).date().isoformat(),'completed':True,'records':[{'student_id':sid,'status':'late'}]}
    aid=ok(c.post(p+'/attendance',headers=t,json=attendance))['id']
    assert ok(c.get('/api/teaching/metrics',headers=t))['attendance_rate']==100
    assert ok(c.get(p+'/workspace',headers=t))['overview']['late']==1
    future=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
    assignment={'title':'心脏结构测验','content':'说明心脏四腔结构','kind':'assignment','status':'draft','due_at':future}
    assignment_id=ok(c.post(p+'/assignments',headers=t,json=assignment))['id']
    assert not ok(c.get(p+'/workspace',headers=st))['assignments']
    assignment['status']='published'
    ok(c.put(p+'/assignments/'+assignment_id,headers=t,json=assignment))
    ok(c.post(p+'/assignments/'+assignment_id+'/submit',headers=st,json={'content':'左右心房与左右心室'}))
    ok(c.put(p+'/assignments/'+assignment_id+'/grades/'+sid,headers=t,json={'score':92,'feedback':'回答正确'}))
    assert ok(c.get(p+'/workspace',headers=st))['assignments'][0]['submissions'][0]['score']==92
    # Due-only denominator: an ongoing assignment must not appear in the completion KPI.
    assert ok(c.get('/api/teaching/metrics',headers=t))['assignment_rate'] is None
    svc=build_service(str(root/'classes.sqlite3'),str(root/'learning.sqlite3'))
    with svc.db() as db:
        db.execute('UPDATE assignments SET due_at=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat(),assignment_id))
    assert ok(c.get('/api/teaching/metrics',headers=t))['assignment_rate']==100
    ok(c.post(p+'/assignments/'+assignment_id+'/submit',headers=st,json={'content':'迟交'}),422)
    task={**assignment,'title':'复习心脏结构','kind':'task'}
    taskid=ok(c.post(p+'/assignments',headers=t,json=task))['id']
    assert ok(c.get('/api/teaching/metrics',headers=t))['progress']==0
    ok(c.post(p+'/assignments/'+taskid+'/submit',headers=st,json={'content':'已完成复习'}))
    assert ok(c.get('/api/teaching/metrics',headers=t))['progress']==100
    announce={'title':'上课通知','content':'请复习心脏结构','status':'published','pinned':True}
    nid=ok(c.post(p+'/announcements',headers=t,json=announce))['id']
    assert len(ok(c.get(p+'/workspace',headers=st))['announcements'])==1
    ok(c.put(p+'/announcements/'+nid,headers=t,json={**announce,'status':'withdrawn'}))
    assert not ok(c.get(p+'/workspace',headers=st))['announcements']
    preview=ok(c.post(p+'/groups/preview?count=1',headers=t))
    assert not ok(c.get(p+'/workspace',headers=t))['groups']
    preview['groups'][0]['leader_id']=sid
    ok(c.put(p+'/groups',headers=t,json=preview))
    assert ok(c.get(p+'/workspace',headers=st))['groups'][0]['student_id']==sid
    ok(c.put(p+'/groups',headers=t,json=preview),422)
    ok(c.put(p+'/groups',headers=t,json={**preview,'replace':True}))
    todo={'title':'备课','priority':3,'done':False,'due_at':future}
    tid=ok(c.post(p+'/todos',headers=t,json=todo))['id']
    ok(c.put(p+'/todos/'+tid,headers=t,json={**todo,'done':True}))
    assert next(x for x in ok(c.get(p+'/workspace',headers=t))['todos'] if x['id']==tid)['done']==1
    file=io.BytesIO()
    from PIL import Image
    Image.new('RGB',(10,10),'white').save(file,format='PNG')
    rid=ok(c.post(p+'/resources?filename=heart.png',headers={**t,'Content-Type':'application/octet-stream'},content=file.getvalue()))['id']
    assert c.get(p+'/resources/'+rid+'/download',headers=st).status_code==404
    ok(c.patch(p+'/resources/'+rid,headers=t,json={'visible':True,'category':'教学图片'}))
    assert c.get(p+'/resources/'+rid+'/download',headers=st).content==file.getvalue()
    ok(c.post(p+'/resources?filename=bad.exe',headers=t,content=b'bad'),422)
    ok(c.post(p+'/resources?filename=bad.png',headers=t,content=b'bad'),422)
    assert c.get(p+'/export/grades',headers=t).status_code==200
    assert c.get(p+'/export/students',headers=st).status_code==403
    assert ok(c.get(p+'/logs',headers=t))['total']>=10
    assert ok(c.get(p+'/workspace',headers=t))['analytics']['has_activity']
    ok(c.delete(p+'/students/'+sid,headers=t))
    assert c.get(p+'/workspace',headers=st).status_code==403
    assert ok(c.get('/api/teaching/metrics',headers=t))['students']==0
    assert ok(c.get(p+'/students/'+sid+'/archive',headers=t))['student_id']==sid
    with svc.db() as db:
        assert db.execute('SELECT COUNT(*) FROM assignment_submissions').fetchone()[0]==2
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
    assert not ok(c.get(p+'/workspace',headers=t))['analytics']['has_activity']
    ok(c.post(p+'/archive',headers=t))
    assert ok(c.get('/api/teaching/metrics',headers=t))['classes']==0
    assert ok(c.get(p+'/workspace',headers=t))['classroom']['archived']==1
    assert c.post(p+'/todos',headers=t,json=todo).status_code==422


def test_permissions_import_validation_and_deduplication(env):
    c,t,st,root=env
    cl=create(c,t); cid=cl['id']; p='/api/teaching/classes/'+cid
    # Second class has a different owner: parameter guessing cannot grant access.
    svc=build_service(str(root/'classes.sqlite3'),str(root/'learning.sqlite3'))
    foreign=main.classroom_service.create_class(teacher_id='other',teacher_account='other',teacher_name='其他教师',name='其他班级')
    for suffix in ['/workspace','/logs','/export/students','/students/someone/archive']:
        assert c.get('/api/teaching/classes/'+foreign['id']+suffix,headers=t).status_code==403
    assert c.get(p+'/workspace',headers=st).status_code==403
    assert c.get('/api/teaching/metrics').status_code==401
    assert c.post('/api/teaching/classes',headers=t,json={'name':'  '}).status_code==422
    assert c.post('/api/teaching/classes',headers=t,json={'name':'越权','teacher_id':'other'}).status_code==403
    students=[r for r in main.auth_service.list_users() if r['role']=='student' and r['status']=='active']
    person=next(r for r in students if r['account']=='student01')
    raw=f"account,name\n{person['account']},{person['name']}\n{person['account']},{person['name']}\nunknown,未知学生\n".encode('utf-8')
    plan=ok(c.post(p+'/students/import-preview?filename=students.csv',headers=t,content=raw))
    assert plan['valid']==1 and plan['rows'][1]['error'] and plan['rows'][2]['error']
    ok(c.post(p+'/students/import',headers=t,json={'token':plan['token']}))
    ok(c.post(p+'/students/import',headers=t,json={'token':plan['token']}),422)
    assert ok(c.get('/api/teaching/metrics',headers=t))['students']==1
    # XLSX path is parsed and validated too.
    from openpyxl import Workbook
    book=Workbook();book.active.append(['account','name']);book.active.append([person['account'],person['name']]);stream=io.BytesIO();book.save(stream)
    plan=ok(c.post(p+'/students/import-preview?filename=students.xlsx',headers=t,content=stream.getvalue()))
    assert plan['valid']==0 and plan['rows'][0]['error']
    assert c.get('/api/teaching/import-template?format=xlsx',headers=t).status_code==200
    today=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    attendance={'title':'错误名单','attendance_date':today,'completed':True,'records':[{'student_id':'other','status':'present'}]}
    ok(c.post(p+'/attendance',headers=t,json=attendance),422)
    assert not ok(c.get(p+'/workspace',headers=t))['attendance'] # transaction rolled back
    # Published rosters remain intact when a student leaves and rejoins.
    ok(c.post(p+'/attendance',headers=t,json={**attendance,'records':[{'student_id':person['id'],'status':'leave'}]}))
    assert ok(c.get('/api/teaching/metrics',headers=t))['attendance_rate'] is None
    ok(c.delete(p+'/students/'+person['id'],headers=t))
    assert main.classroom_service.list_for_teacher(cl['teacher_id'])[0]['student_count']==0
    ok(c.post('/api/classrooms/join',headers=st,json={'code':cl['code']}))
    assert main.classroom_service.is_member(cid,person['id'])
    assert len(ok(c.get(p+'/workspace',headers=st))['attendance'][0]['records'])==1


def test_migration_is_repeatable_and_preserves_old_database(tmp_path):
    from backend.app.services.teaching_service import TeachingService
    classes=ClassroomService(tmp_path/'old.sqlite3')
    cl=classes.create_class(teacher_id='t',teacher_account='t',teacher_name='教师',name='历史班级')
    classes.join_by_code(student_id='s',student_account='s',student_name='学生',code=cl['code'])
    classes.add_guidance(class_id=cl['id'],student_id='s',author_id='t',author_name='教师',source='teacher',content='历史建议')
    TeachingService(classes,tmp_path/'learning.sqlite3')
    TeachingService(classes,tmp_path/'learning.sqlite3')
    assert classes.class_detail('t',cl['id'])['student_count']==1
    assert classes.list_guidance(student_id='s')[0]['content']=='历史建议'
    assert (tmp_path/'old.pre-teaching-v1.sqlite3').exists()
    with sqlite3.connect(tmp_path/'old.sqlite3') as db:
        assert db.execute('SELECT COUNT(*) FROM teaching_schema_versions').fetchone()[0]==1


def test_student_isolation_and_distinct_students(env):
    c,t,st,root=env
    other,token=main.auth_service.register('peer01','另一学生','peer@example.test','peer123456','student')
    main.auth_service.verify_email(token)
    login=ok(c.post('/api/auth/login',json={'account':'peer01','password':'peer123456','role':'student'}))
    peer={'Authorization':'Bearer '+login['token']}
    c1=create(c,t,'甲班');c2=create(c,t,'乙班')
    for cl in (c1,c2):
        ok(c.post('/api/classrooms/join',headers=st,json={'code':cl['code']}))
    ok(c.post('/api/classrooms/join',headers=peer,json={'code':c1['code']}))
    assert ok(c.get('/api/teaching/metrics',headers=t))['students']==2
    p='/api/teaching/classes/'+c1['id']
    a=ok(c.post(p+'/assignments',headers=t,json={'title':'共同作业','content':'回答问题','status':'published','due_at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}))
    ok(c.post(p+'/assignments/'+a['id']+'/submit',headers=peer,json={'content':'另一学生的私有答案'}))
    own=ok(c.get(p+'/workspace',headers=st))
    assert 'students' not in own and 'analytics' not in own and 'logs' not in own
    assert len(own['assignments'][0]['submissions'])==1
    assert own['assignments'][0]['submissions'][0]['content'] is None
    assert '私有答案' not in str(own)
    assert c.get(p+'/students/'+other['id']+'/archive',headers=st).status_code==403
    assert c.put(p+'/assignments/'+a['id']+'/grades/'+other['id'],headers=st,json={'score':100}).status_code==403
    assert c.get('/api/teaching/classes/'+c2['id']+'/workspace',headers=peer).status_code==403


def test_concurrent_first_load_migrates_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    classes=ClassroomService(tmp_path/'concurrent.sqlite3')
    args=(str(classes.database_path),str(tmp_path/'learning.sqlite3'))
    with ThreadPoolExecutor(max_workers=8) as pool:
        services=list(pool.map(lambda _:build_service(*args),range(16)))
    assert all(s is services[0] for s in services)
    with services[0].db() as db:
        assert len([r for r in db.execute('PRAGMA table_info(classrooms)') if r[1]=='major'])==1
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_join_application_and_todo_lifecycle(env):
    c,t,st,_=env
    cl=create(c,t)
    p='/api/teaching/classes/'+cl['id']
    ok(c.post('/api/teaching/join-requests',headers=st,json={'code':cl['code']}))
    w=ok(c.get(p+'/workspace',headers=t))
    assert len(w['applications'])==1
    todo=next(t for t in w['todos'] if t['id'].startswith('join-'))
    assert todo['tab']=='students' and not todo.get('custom')
    rid=w['applications'][0]['id']
    assert c.post(p+'/join-requests/'+rid+'/decision',headers=st,json={'approve':True}).status_code==403
    assert c.get(p+'/workspace',headers=st).status_code==403
    ok(c.post(p+'/join-requests/'+rid+'/decision',headers=t,json={'approve':True}))
    w=ok(c.get(p+'/workspace',headers=t))
    assert len(w['students'])==1 and not w['applications']
    assert not any(t['id'].startswith('join-') for t in w['todos'])
    assert ok(c.get('/api/teaching/join-requests/mine',headers=st))['items'][0]['status']=='approved'
    second=create(c,t,'申请被拒绝的班级');p2='/api/teaching/classes/'+second['id']
    ok(c.post('/api/teaching/join-requests',headers=st,json={'code':second['code']}))
    rid=ok(c.get(p2+'/workspace',headers=t))['applications'][0]['id']
    ok(c.post(p2+'/join-requests/'+rid+'/decision',headers=t,json={'approve':False}))
    assert c.get(p2+'/workspace',headers=st).status_code==403
    assert not ok(c.get(p2+'/workspace',headers=t))['students']
