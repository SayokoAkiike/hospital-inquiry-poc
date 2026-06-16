from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    audit,
    auth,
    escalations,
    kpi,
    messages,
    notifications,
    patients,
    tickets,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["認証"])
api_router.include_router(patients.router, prefix="/patients", tags=["患者"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["チケット"])
api_router.include_router(messages.router, prefix="/tickets", tags=["メッセージ"])
api_router.include_router(escalations.router, prefix="/tickets", tags=["エスカレーション"])
api_router.include_router(kpi.router, prefix="/kpi", tags=["KPI"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["監査ログ"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理"])
