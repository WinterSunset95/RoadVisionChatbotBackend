from fastapi import APIRouter
from app.modules.health import health
from app.modules.askai.router import router as askai_router
from app.modules.auth.route import router as auth_router

api_v1_router = APIRouter()

# General v1 endpoints
api_v1_router.include_router(health.router)

# Feature module routers
api_v1_router.include_router(auth_router, prefix="/auth")
api_v1_router.include_router(askai_router, prefix="/askai")

# In the future, you can add other module routers here:
# from app.modules.dashboard.router import router as dashboard_router
# api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
