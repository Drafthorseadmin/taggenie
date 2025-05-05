from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import json
import os
from app.tag_suggester import suggest_tags
from app.asset_tags_suggester import suggest_asset_tags

app = FastAPI(title="Template Tagging Helper")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load tag hierarchy from JSON file
def load_tag_hierarchy():
    with open("app/tag_hierarchy.json", "r") as f:
        return json.load(f)

# Tag hierarchy structure
TAG_HIERARCHY = load_tag_hierarchy()

class TagSuggestion(BaseModel):
    category: str
    suggested_tags: List[str]
    confidence: float

class TagRequest(BaseModel):
    description: str = ""  # Make description optional
    type: str = "template"  # Default to template type
    filename: str = ""  # Add filename field

@app.get("/")
async def root():
    return {"message": "Template Tagging Helper API"}

@app.get("/tags")
async def get_tag_hierarchy():
    return TAG_HIERARCHY

@app.post("/api/suggest_tags")
async def get_tag_suggestions(request: TagRequest):
    try:
        # If filename is provided, use filename-based suggestion
        if request.filename:
            return suggest_tags_from_filename(request.filename)
        
        # Otherwise use description-based suggestion
        if request.type == "template":
            return suggest_tags(request.description)
        elif request.type == "asset":
            return suggest_asset_tags(request.description)
        else:
            raise HTTPException(status_code=400, detail="Invalid type. Must be either 'template' or 'asset'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 