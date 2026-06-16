from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="Hospital Inquiry PoC",
    description="病院向け患者問い合わせ・エスカレーション管理システム",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
