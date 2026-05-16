from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TrueLens Backend",
    description="ML-powered Content Verification API",
    version="1.0.0",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "TrueLens Backend API is running"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

app.include_router(api_router, prefix="/api/v1")
