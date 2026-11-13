import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Header, Request, Query, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ..config import ROOT_DIR
from ..services.access_audit_service import AccessAuditService

router = APIRouter()
access_service = AccessAuditService(Path(ROOT_DIR)/'data'/'access_audit.sqlite3')


def record(request, *, user=None, path=None, kind='operation', visitor_id='', status=200):
    try:
        # request.client is resolved by the server's trusted-proxy configuration.
        # Never trust arbitrary forwarded-IP headers directly here.
        access_service.record(user=user,ip=request.client.host if request.client else '',
                              path=path or request.url.path,method='GET' if kind in {'page_view','heartbeat'} else request.method,status=status,
                              kind=kind,visitor_id=visitor_id,user_agent=request.headers.get('user-agent',''))
    except Exception:
        logging.getLogger(__name__).exception('Access audit write failed')


class Visit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    path: str = Field(min_length=1,max_length=1000)
    visitor_id: str = Field(min_length=16,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    kind: Literal['page_view','heartbeat'] = 'page_view'

    @field_validator('path')
    @classmethod
    def valid_path(cls, value):
        if not value.startswith('/') or value.startswith('//') or any(ord(c)<32 for c in value):
            raise ValueError('仅记录站内页面路径')
        return value.split('?')[0].split('#')[0]


@router.post('/api/access/visit',status_code=204)
def visit(payload: Visit, request: Request, authorization: str | None = Header(default=None)):
    from ..main import optional_user
    record(request,user=optional_user(authorization),path=payload.path,kind=payload.kind,visitor_id=payload.visitor_id)


@router.get('/api/admin/access-audit')
def logs(q: str = Query('',max_length=100), kind: Literal['','page_view','login','operation'] = '',
         page: int = Query(1,ge=1),size: int = Query(30,ge=1,le=100), role: Literal['','guest','student','teacher','admin','super_admin']='',
         result: Literal['','success','failure']='',since: datetime | None=None,until: datetime | None=None,authorization: str | None = Header(default=None)):
    from ..main import require_role
    require_role(authorization,{'admin','super_admin'})
    if any(v is not None and v.tzinfo is None for v in [since,until]):
        raise HTTPException(422,'筛选时间必须包含时区')
    if since and until and since>until:
        raise HTTPException(422,'开始时间不能晚于结束时间')
    stamp=lambda v:v.astimezone(timezone.utc).isoformat(timespec='milliseconds') if v else ''
    return access_service.list(q,kind,page,size,role,result,stamp(since),stamp(until))
