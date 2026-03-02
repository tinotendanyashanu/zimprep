from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.questions import router as questions_router
from routes.attempts import router as attempts_router

app = FastAPI(title="Zimprep Skeleton API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(questions_router)
app.include_router(attempts_router)

@app.get("/")
async def root():
    return {"message": "Zimprep Skeleton API running"}
