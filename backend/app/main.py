from fastapi import FastAPI
from app.infrastructure.database.mongo import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
)
from app.api.auth_router import router as auth_router  # 🔹 Import Auth router
from app.api.onboarding_router import router as onboarding_router # 🔹 Import Onboarding router
from app.api.jobs_router import router as jobs_router # 🔹 Import Jobs router

app = FastAPI(title="DevPulse Backend")


# 🔄 Startup event
@app.on_event("startup")
async def startup():
    await connect_to_mongo()


# 🔄 Shutdown event
@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()


# ❤️ Health check
@app.get("/health")
async def health_check():
    try:
        db = get_database()

        if db is None:
            return {"status": "error", "database": "not initialized"}

        # ping MongoDB
        await db.command("ping")

        return {"status": "ok", "database": "connected"}

    except Exception as e:
        return {"status": "error", "database": str(e)}


# 🔹 Include routers
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(jobs_router)