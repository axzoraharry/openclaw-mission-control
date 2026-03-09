"""FastAPI backend for test-saas."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="test-saas", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to test-saas API"}


@app.get("/healthz")
async def health():
    return {"status": "healthy"}


@app.get("/api/v1/items")
async def get_items():
    return {"items": [{"id": 1, "name": "Sample Item"}]}
