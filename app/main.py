from fastapi import FastAPI

app = FastAPI(
    title="Hospital Inquiry PoC",
    description="病院向け患者問い合わせ・エスカレーション管理システム",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
