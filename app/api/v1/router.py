from fastapi import APIRouter

from app.api.v1.endpoints import auth, patients, tickets, messages, escalations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["認証"])
api_router.include_router(patients.router, prefix="/patients", tags=["患者"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["チケット"])
api_router.include_router(messages.router, prefix="/tickets", tags=["メッセージ"])
api_router.include_router(escalations.router, prefix="/tickets", tags=["エスカレーション"])
