from fastapi import FastAPI
from src.app.routes import router
from src.app.database import init_db

app = FastAPI(
    title="LLM 对话服务",
    description="通过阿里百炼 API 提供大模型对话能力",
    version="0.1.0",
)

app.include_router(router, prefix="/api/llm", tags=["llm"])


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "llm-service"}
