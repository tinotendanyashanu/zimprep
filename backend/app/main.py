from fastapi import FastAPI

app = FastAPI(title="ZimPrep API")

@app.get("/")
async def root():
    return {"message": "ZimPrep API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
