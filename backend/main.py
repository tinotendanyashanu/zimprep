import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import admin, papers, sessions, attempts, students, parents, subscriptions, webhooks, waitlist, employees

load_dotenv()

app = FastAPI(
    title="ZimPrep API",
    description="Backend API for the ZimPrep ZIMSEC exam preparation platform",
    version="1.0.0",
)

# CORS — allow frontend origin(s)
origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
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
app.include_router(parents.router, prefix="/parents", tags=["parents"])
app.include_router(subscriptions.router, tags=["subscriptions"])
app.include_router(webhooks.router, tags=["webhooks"])
app.include_router(waitlist.router, tags=["waitlist"])
app.include_router(employees.router, prefix="/admin/employees", tags=["employees"])


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
