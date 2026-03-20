from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.questions import router as questions_router
from routes.attempts import router as attempts_router
from routes.admin import router as admin_router
from routes.marking import router as marking_router
from routes.ocr import router as ocr_router
from routes.subscription import router as subscription_router
from routes.catalog import router as catalog_router
from routes.students import router as students_router
from core.config import settings

app = FastAPI(title="Zimprep API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(questions_router)
app.include_router(attempts_router)
app.include_router(admin_router)
app.include_router(marking_router)
app.include_router(ocr_router)
app.include_router(subscription_router)
app.include_router(catalog_router)
app.include_router(students_router)

@app.get("/")
async def root():
    return {"message": "Zimprep API running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
