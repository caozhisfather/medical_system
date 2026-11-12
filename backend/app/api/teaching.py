"""Authenticated teaching workflows, sharing the existing class and auth stores."""
from __future__ import annotations

import csv
import io
import json
import random
import sqlite3
import zipfile
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from threading import RLock
from typing import Literal

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..services.teaching_service import TeachingService, TZ, uid, _now


class TeachingRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request):
            try:
                return await original(request)
            except PermissionError as exc:
                raise HTTPException(403, str(exc)) from exc
            except KeyError as exc:
                raise HTTPException(404, str(exc).strip("'")) from exc
            except (ValueError, sqlite3.IntegrityError) as exc:
                raise HTTPException(422, str(exc)) from exc
        return handler


router = APIRouter(prefix='/api/teaching', tags=['班级教学管理'], route_class=TeachingRoute)


def main():
    from .. import main as module
    return module


_initialization_lock = RLock()


@lru_cache(maxsize=8)
def _build_service(class_path, learning_path):
    from ..services.classroom_service import ClassroomService
    return TeachingService(ClassroomService(Path(class_path)), Path(learning_path))


def build_service(class_path, learning_path):
    # functools.lru_cache permits concurrent cache misses; migrations must run once.
    with _initialization_lock:
        return _build_service(class_path, learning_path)


def service():
    m = main()
    return build_service(str(m.classroom_service.database_path), str(m.anatomy_learning_service.database_path))


def user(authorization: str | None = Header(default=None)):
    return main().require_role(authorization, {'teacher', 'admin', 'super_admin', 'student'})


def teacher(u=Depends(user)):
    if u.role == 'student':
        raise HTTPException(403, '只有教师或管理员可以执行此操作')
    return u


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class ClassInput(Model):
    name: str = Field(min_length=2, max_length=60)
    description: str = Field(default='', max_length=500)
    major: str = Field(default='', max_length=80)
    grade: str = Field(default='', max_length=30)
    semester: str = Field(default='', max_length=50)
    teacher_id: str = ''


class Record(Model):
    student_id: str
    status: Literal['present', 'late', 'leave', 'absent']


class AttendanceInput(Model):
    title: str = Field(min_length=1, max_length=120)
    attendance_date: date
    completed: bool = False
    records: list[Record] = Field(default_factory=list, max_length=2000)


class AssignmentInput(Model):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=20000)
    kind: Literal['assignment', 'task'] = 'assignment'
    status: Literal['draft', 'published'] = 'draft'
    due_at: datetime

    @field_validator('due_at')
    @classmethod
    def aware(cls, v):
        if not v.tzinfo:
            raise ValueError('截止时间必须包含时区')
        return v.astimezone(timezone.utc)


class AnnouncementInput(Model):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=20000)
    status: Literal['draft', 'published', 'withdrawn'] = 'draft'
    pinned: bool = False


class Group(Model):
    name: str = Field(min_length=1, max_length=60)
    leader_id: str = ''
    members: list[str] = Field(default_factory=list, max_length=2000)


class GroupInput(Model):
    groups: list[Group] = Field(max_length=200)
    replace: bool = False


class TodoInput(Model):
    title: str = Field(min_length=1, max_length=200)
    due_at: datetime | None = None
    priority: int = Field(default=1, ge=0, le=3)
    done: bool = False

    @field_validator('due_at')
    @classmethod
    def aware(cls, v):
        if v and not v.tzinfo:
            raise ValueError('截止时间必须包含时区')
        return v.astimezone(timezone.utc) if v else None


def serialized(payload):
    result = payload.model_dump(mode='json')
    if isinstance(payload, (AssignmentInput, TodoInput)) and payload.due_at:
        result['due_at'] = payload.due_at.isoformat(timespec='seconds')
    return result


@router.get('/classes')
def classes(q: str = '', major: str = '', grade: str = '', semester: str = '', status: str = '', page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100), u=Depends(user)):
    return service().list_classes(u, q, major, grade, semester, status, page, size)


@router.get('/teachers')
def teachers(u=Depends(teacher)):
    if u.role == 'teacher':
        return {'items': [{'id': u.id, 'name': u.name, 'account': u.account}]}
    return {'items': [{k: r[k] for k in ('id', 'name', 'account')} for r in main().auth_service.list_users() if r['role']=='teacher' and r['status']=='active']}


class JoinRequest(Model):
    code: str = Field(min_length=4,max_length=16)


@router.post('/join-requests')
def request_join(p: JoinRequest, u=Depends(user)):
    if u.role!='student':
        raise PermissionError('只有学生可以申请加入班级')
    s=service()
    with s.db() as db:
        cl=db.execute('SELECT * FROM classrooms WHERE code=? COLLATE NOCASE AND archived=0',(p.code,)).fetchone()
        if not cl:
            raise KeyError('邀请码无效或班级已归档')
        if db.execute('SELECT 1 FROM classroom_memberships WHERE class_id=? AND student_id=? AND active=1',(cl['id'],u.id)).fetchone():
            raise ValueError('你已经在该班级中')
        db.execute("INSERT INTO class_join_requests VALUES(?,?,?,?,?,'pending',NULL,?,?) ON CONFLICT(class_id,student_id) DO UPDATE SET status='pending',reviewed_by=NULL,updated_at=excluded.updated_at",(uid(),cl['id'],u.id,u.account,u.name,_now(),_now()))
        s.log(db,u,cl['id'],'join_request','提交入班申请')
    return {'ok':True}


@router.get('/join-requests/mine')
def own_requests(u=Depends(user)):
    if u.role!='student':
        raise PermissionError('只有学生可以查看个人入班申请')
    s=service()
    with s.db() as db:
        return {'items':[dict(r) for r in db.execute('SELECT r.id,r.status,r.updated_at,c.name class_name FROM class_join_requests r JOIN classrooms c ON c.id=r.class_id WHERE r.student_id=? ORDER BY r.updated_at DESC',(u.id,))]}


class Decision(Model):
    approve: bool


@router.post('/classes/{cid}/join-requests/{rid}/decision')
def decide_request(cid: str, rid: str, p: Decision, u=Depends(teacher)):
    s=service()
    with s.db() as db:
        s.access(db,u,cid,write=True)
        row=db.execute("SELECT * FROM class_join_requests WHERE id=? AND class_id=? AND status='pending'",(rid,cid)).fetchone()
        if not row:
            raise KeyError('申请不存在或已处理')
        if p.approve:
            person=next((r for r in main().auth_service.list_users() if r['id']==row['student_id'] and r['role']=='student' and r['status']=='active'),None)
            if not person:
                raise ValueError('申请学生账号已失效')
            s.add_members(db,u,cid,[person])
        db.execute('UPDATE class_join_requests SET status=?,reviewed_by=?,updated_at=? WHERE id=?',('approved' if p.approve else 'rejected',u.id,_now(),rid))
        s.log(db,u,cid,'join_request',('批准' if p.approve else '拒绝')+'入班申请：'+row['student_name'])
    return {'ok':True}


def owning_teacher(u, requested, cid=None):
    if u.role == 'teacher':
        if requested and requested != u.id:
            raise PermissionError('教师不能将班级指派给其他教师')
        return u.model_dump()
    if not requested and cid:
        s = service()
        with s.db() as db:
            requested = s.access(db,u,cid)['teacher_id']
    row = next((r for r in main().auth_service.list_users() if r['id']==requested and r['role']=='teacher' and r['status']=='active'), None)
    if not row:
        raise ValueError('请选择有效的任课教师')
    return row


@router.post('/classes')
def create_class(p: ClassInput, u=Depends(teacher)):
    return service().save_class(u, p.model_dump(), owning_teacher(u,p.teacher_id))


@router.put('/classes/{cid}')
def edit_class(cid: str, p: ClassInput, u=Depends(teacher)):
    return service().save_class(u,p.model_dump(),owning_teacher(u,p.teacher_id,cid),cid)


@router.post('/classes/{cid}/archive')
def archive(cid: str, u=Depends(teacher)):
    service().archive(u,cid)
    return {'ok': True}


@router.get('/metrics')
def metrics(u=Depends(teacher)):
    return service().metrics(u)


@router.get('/classes/{cid}/workspace')
def workspace(cid: str, days: int = Query(30, ge=1, le=90), start: date | None = None, end: date | None = None, attendance_date: date | None = None, u=Depends(user)):
    end = end or datetime.now(TZ).date()
    start = start or end-timedelta(days=days-1)
    if start > end or (end-start).days > 365:
        raise ValueError('日期范围必须为 1～366 天')
    return service().workspace(u,cid,start.isoformat(),end.isoformat(),(attendance_date or datetime.now(TZ).date()).isoformat())


@router.get('/classes/{cid}/students/{sid}/archive')
def student_archive(cid: str, sid: str, u=Depends(user)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,student=True)
        if u.role == 'student' and sid != u.id:
            raise PermissionError('只能查看自己的学习档案')
        row = db.execute('SELECT * FROM classroom_memberships WHERE class_id=? AND student_id=?', (cid,sid)).fetchone()
        if not row:
            raise KeyError('班级中没有该学生的记录')
        snapshot = main().student_learning_snapshot(row['student_account'])
        if not snapshot['total_attempts']:
            snapshot['average_score'] = None
        return {**dict(row), **snapshot}


@router.delete('/classes/{cid}/students/{sid}')
def remove(cid: str, sid: str, u=Depends(teacher)):
    service().remove_member(u,cid,sid)
    return {'ok': True}


def csv_response(rows, filename):
    output = io.StringIO()
    def cell(value):
        text = '' if value is None else str(value)
        return "'"+text if text.startswith(('=', '+', '-', '@', '\t', '\r')) else text
    csv.writer(output).writerows([[cell(c) for c in row] for row in rows])
    return Response(output.getvalue().encode('utf-8-sig'), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@router.get('/import-template')
def template(format: Literal['csv', 'xlsx'] = 'csv', u=Depends(teacher)):
    if format == 'csv':
        return csv_response([['account','name']], 'students-template.csv')
    from openpyxl import Workbook
    book = Workbook()
    book.active.append(['account','name'])
    output = io.BytesIO()
    book.save(output)
    return Response(output.getvalue(),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="students-template.xlsx"'})


async def limited_body(request, limit):
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > limit:
            raise HTTPException(413, f'文件超过 {limit//1024//1024} MB 限制')
    if not data:
        raise ValueError('文件不能为空')
    return bytes(data)


def safe_zip(data):
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        if len(z.infolist()) > 2000 or sum(i.file_size for i in z.infolist()) > 100*1024*1024:
            raise ValueError('压缩文档展开后过大')
        return z
    except zipfile.BadZipFile as exc:
        raise ValueError('无效的 Office 文档') from exc


@router.post('/classes/{cid}/students/import-preview')
async def preview(cid: str, request: Request, filename: str = Query(..., max_length=200), u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,write=True)
    data = await limited_body(request, 5*1024*1024)
    ext = Path(filename).suffix.lower()
    try:
        if ext == '.csv':
            rows = list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))
        elif ext == '.xlsx':
            from openpyxl import load_workbook
            safe_zip(data).close()
            book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            rows = []
            try:
                for row in book.active.iter_rows(values_only=True):
                    rows.append(list(row))
                    if len(rows) > 2001:
                        raise ValueError('每次最多导入 2000 行')
            finally:
                book.close()
        else:
            raise ValueError('只支持 UTF-8 CSV 或 XLSX 文件')
    except (UnicodeError, csv.Error) as exc:
        raise ValueError('无法读取，请使用 UTF-8 CSV 或下载模板') from exc
    if not rows or len(rows) > 2001 or [str(v or '').strip() for v in rows[0][:2]] != ['account','name']:
        raise ValueError('表头必须为 account,name，每次最多 2000 行')
    users = {r['account']: r for r in main().auth_service.list_users() if r['role']=='student' and r['status']=='active'}
    with s.db() as db:
        existing = {r['student_id'] for r in s.roster(db,cid)}
        seen, results = set(), []
        for number, row in enumerate(rows[1:],2):
            if not any(v is not None and str(v).strip() for v in row):
                continue
            account = str(row[0] or '').strip()
            name = str(row[1] or '').strip() if len(row)>1 else ''
            person = users.get(account)
            error = '账号尚未注册或不是有效学生' if not person else '姓名与账号不一致' if name and name != person['name'] else '文件中重复账号' if account in seen else '该学生已在班级中' if person['id'] in existing else ''
            results.append({'row':number,'account':account,'name':person['name'] if person else name,'id': person['id'] if person else '', 'error':error})
            seen.add(account)
        token = uid()
        db.execute('INSERT INTO class_import_previews VALUES(?,?,?,?,?,0)', (token,cid,u.id,json.dumps(results,ensure_ascii=False),_now()))
        return {'token':token,'rows':results,'valid':sum(not r['error'] for r in results)}


class ConfirmImport(Model):
    token: str


@router.post('/classes/{cid}/students/import')
def confirm_import(cid: str, p: ConfirmImport, u=Depends(teacher)):
    s = service()
    current = {r['id']:r for r in main().auth_service.list_users() if r['role']=='student' and r['status']=='active'}
    with s.db() as db:
        s.access(db,u,cid,write=True)
        row = db.execute('SELECT * FROM class_import_previews WHERE id=? AND class_id=? AND teacher_id=? AND used=0',(p.token,cid,u.id)).fetchone()
        if not row or datetime.fromisoformat(row['created_at']) < datetime.now(timezone.utc)-timedelta(minutes=30):
            raise ValueError('预览已过期或已使用，请重新上传')
        existing = {r['student_id'] for r in s.roster(db,cid)}
        people = [current[r['id']] for r in json.loads(row['payload']) if not r['error'] and r['id'] in current and r['id'] not in existing]
        if not people:
            raise ValueError('没有可以导入的新学生')
        s.add_members(db,u,cid,people)
        db.execute('UPDATE class_import_previews SET used=1 WHERE id=?',(p.token,))
        return {'imported':len(people)}


@router.get('/classes/{cid}/export/{kind}')
def export(cid: str, kind: Literal['students','attendance','grades'], u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid)
        if kind == 'students':
            rows = [['账号','姓名','加入时间'], *[[r['student_account'],r['student_name'],r['joined_at']] for r in s.roster(db,cid)]]
        elif kind == 'attendance':
            rows = [['活动','日期','账号','姓名','状态'], *[list(r) for r in db.execute('SELECT s.title,s.attendance_date,m.student_account,m.student_name,r.status FROM attendance_sessions s JOIN attendance_records r ON r.session_id=s.id JOIN classroom_memberships m ON m.class_id=r.class_id AND m.student_id=r.student_id WHERE s.class_id=? ORDER BY s.attendance_date DESC',(cid,))]]
        else:
            rows = [['作业','账号','姓名','提交时间','成绩','教师评语'], *[list(r) for r in db.execute('SELECT a.title,m.student_account,m.student_name,s.submitted_at,s.score,s.feedback FROM assignments a JOIN assignment_recipients r ON r.assignment_id=a.id JOIN classroom_memberships m ON m.class_id=r.class_id AND m.student_id=r.student_id LEFT JOIN assignment_submissions s ON s.assignment_id=r.assignment_id AND s.student_id=r.student_id WHERE a.class_id=?',(cid,))]]
        return csv_response(rows,kind+'.csv')


@router.post('/classes/{cid}/attendance')
@router.put('/classes/{cid}/attendance/{item_id}')
def attendance(cid: str, p: AttendanceInput, item_id: str | None = None, u=Depends(teacher)):
    return service().attendance(u,cid,serialized(p),item_id)


@router.post('/classes/{cid}/assignments')
@router.put('/classes/{cid}/assignments/{item_id}')
def assignment(cid: str, p: AssignmentInput, item_id: str | None = None, u=Depends(teacher)):
    return service().assignment(u,cid,serialized(p),item_id)


class Submission(Model):
    content: str = Field(min_length=1,max_length=20000)


@router.post('/classes/{cid}/assignments/{aid}/submit')
def submit(cid: str, aid: str, p: Submission, u=Depends(user)):
    if u.role != 'student':
        raise PermissionError('只有接收作业的学生可以提交')
    service().submit(u,cid,aid,p.content)
    return {'ok':True}


class Grade(Model):
    score: float = Field(ge=0,le=100,allow_inf_nan=False)
    feedback: str = Field(default='',max_length=2000)


@router.put('/classes/{cid}/assignments/{aid}/grades/{sid}')
def grade(cid: str, aid: str, sid: str, p: Grade, u=Depends(teacher)):
    service().grade(u,cid,aid,sid,p.score,p.feedback)
    return {'ok':True}


@router.post('/classes/{cid}/announcements')
@router.put('/classes/{cid}/announcements/{item_id}')
def announcement(cid: str, p: AnnouncementInput, item_id: str | None = None, u=Depends(teacher)):
    return service().announcement(u,cid,serialized(p),item_id)


@router.post('/classes/{cid}/groups/preview')
def group_preview(cid: str, count: int = Query(2,ge=1,le=200), u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,write=True)
        ids = [r['student_id'] for r in s.roster(db,cid)]
        if not ids or count > len(ids):
            raise ValueError('组数不能超过在籍学生人数')
        random.SystemRandom().shuffle(ids)
        return {'groups':[{'name':f'第 {i+1} 组','members':ids[i::count],'leader_id':''} for i in range(count)]}


@router.put('/classes/{cid}/groups')
def groups(cid: str, p: GroupInput, u=Depends(teacher)):
    service().save_groups(u,cid,[g.model_dump() for g in p.groups],p.replace)
    return {'ok':True}


@router.post('/classes/{cid}/todos')
@router.put('/classes/{cid}/todos/{item_id}')
def todo(cid: str, p: TodoInput, item_id: str | None = None, u=Depends(teacher)):
    return service().todo(u,cid,serialized(p),item_id)


@router.get('/classes/{cid}/logs')
def logs(cid: str, page: int = Query(1,ge=1), size: int = Query(30,ge=1,le=100), u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid)
        return {'items':[dict(r) for r in db.execute('SELECT * FROM class_activity_logs WHERE class_id=? ORDER BY created_at DESC,rowid DESC LIMIT ? OFFSET ?',(cid,size,(page-1)*size))], 'total':db.execute('SELECT COUNT(*) FROM class_activity_logs WHERE class_id=?',(cid,)).fetchone()[0]}


ALLOWED = {'.pdf','.doc','.docx','.ppt','.pptx','.xls','.xlsx','.png','.jpg','.jpeg','.webp'}


def validate_file(data, ext):
    if ext not in ALLOWED:
        raise ValueError('不支持此文件格式，可上传 PDF、Office 文档和 PNG/JPEG/WebP 图片')
    if ext == '.pdf' and not data.startswith(b'%PDF-'):
        raise ValueError('PDF 文件内容与扩展名不符')
    if ext in {'.doc','.ppt','.xls'} and not data.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('Office 文件内容与扩展名不符')
    if ext in {'.docx','.pptx','.xlsx'}:
        with safe_zip(data) as z:
            prefix = {'.docx':'word/', '.pptx':'ppt/', '.xlsx':'xl/'}[ext]
            if '[Content_Types].xml' not in z.namelist() or not any(n.startswith(prefix) for n in z.namelist()):
                raise ValueError('Office 文件内容与扩展名不符')
            if any(n.lower().endswith(('vbaproject.bin','.exe','.js')) for n in z.namelist()):
                raise ValueError('不接受包含宏或可执行附件的文档')
    if ext in {'.png','.jpg','.jpeg','.webp'}:
        from PIL import Image
        try:
            with Image.open(io.BytesIO(data)) as im:
                expected = {'.png':'PNG','.jpg':'JPEG','.jpeg':'JPEG','.webp':'WEBP'}[ext]
                if im.format != expected or im.width*im.height > 40000000:
                    raise ValueError('图片格式不符或尺寸过大')
                im.verify()
        except Exception as exc:
            raise ValueError('无法读取该图片') from exc


@router.post('/classes/{cid}/resources')
async def upload(cid: str, request: Request, filename: str = Query(...,min_length=1,max_length=180), category: str = Query('课件',max_length=60), visible: bool = False, u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,write=True)
    name = filename.replace('\\','/').split('/')[-1]
    if any(ord(c)<32 for c in name):
        raise ValueError('文件名包含非法字符')
    ext = Path(name).suffix.lower()
    data = await limited_body(request,25*1024*1024)
    validate_file(data,ext)
    item_id, storage = uid(),uid()+ext
    s.files.mkdir(parents=True,exist_ok=True)
    path = s.files/storage
    try:
        with s.db() as db:
            s.access(db,u,cid,write=True)
            path.write_bytes(data)
            db.execute('INSERT INTO class_resources VALUES(?,?,?,?,?,?,?,?,?,0,?,?)',(item_id,cid,name,category,int(visible),storage,len(data),u.id,u.name,_now(),_now()))
            s.log(db,u,cid,'resource','上传教学资料：'+name)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {'id':item_id}


class ResourceInput(Model):
    category: str = Field(default='课件',max_length=60)
    visible: bool


@router.patch('/classes/{cid}/resources/{rid}')
def resource_visibility(cid: str, rid: str, p: ResourceInput, u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,write=True)
        if not db.execute('UPDATE class_resources SET visible=?,category=?,updated_at=? WHERE id=? AND class_id=? AND deleted=0',(int(p.visible),p.category,_now(),rid,cid)).rowcount:
            raise KeyError('资料不存在')
        s.log(db,u,cid,'resource','更新资料分类与学生可见权限')
    return {'ok':True}


@router.delete('/classes/{cid}/resources/{rid}')
def resource_delete(cid: str, rid: str, u=Depends(teacher)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,write=True)
        if not db.execute('UPDATE class_resources SET deleted=1,updated_at=? WHERE id=? AND class_id=? AND deleted=0',(_now(),rid,cid)).rowcount:
            raise KeyError('资料不存在')
        s.log(db,u,cid,'resource','移除教学资料（不再对学生提供下载）')
    return {'ok':True}


@router.get('/classes/{cid}/resources/{rid}/download')
def download(cid: str, rid: str, u=Depends(user)):
    s = service()
    with s.db() as db:
        s.access(db,u,cid,student=True)
        row = db.execute('SELECT * FROM class_resources WHERE id=? AND class_id=? AND deleted=0',(rid,cid)).fetchone()
        if not row or (u.role=='student' and not row['visible']):
            raise KeyError('资料不存在或未对学生开放')
        path = s.files/row['storage_name']
        if not path.is_file():
            raise KeyError('资料文件缺失，请联系教师')
        return FileResponse(path,filename=row['name'],media_type='application/octet-stream',headers={'X-Content-Type-Options':'nosniff'})
