import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import admin, papers, sessions, attempts, students

load_dotenv()

app = FastAPI(
    title="ZimPrep API",
    description="Backend API for the ZimPrep ZIMSEC exam preparation platform",
    version="1.0.0",
)

# CORS — allow frontend origin(s)
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(attempts.router, prefix="/attempts", tags=["attempts"])
app.include_router(students.router, prefix="/students", tags=["students"])


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
