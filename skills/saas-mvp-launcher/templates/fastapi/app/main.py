"""FastAPI backend for {{PROJECT_NAME}}."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="{{PROJECT_NAME}}",
    description="API for {{PROJECT_NAME}}",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

# In-memory storage
items: List[Item] = []


@app.get("/")
async def root():
    return {
        "message": "Welcome to {{PROJECT_NAME}} API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/healthz")
async def health():
    return {"status": "healthy", "service": "{{PROJECT_NAME}}"}


@app.get("/api/v1/items", response_model=List[Item])
async def get_items():
    return items


@app.post("/api/v1/items", response_model=Item)
async def create_item(item: ItemCreate):
    new_item = Item(
        id=len(items) + 1,
        name=item.name,
        description=item.description,
        price=item.price
    )
    items.append(new_item)
    return new_item


@app.get("/api/v1/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/api/v1/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item.id == item_id:
            items.pop(i)
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
