import json
from typing import List, Dict
import os
import requests
from dotenv import load_dotenv
from itertools import islice
from functools import lru_cache
import time

# Load environment variables from the root directory
load_dotenv(override=True)

# Hugging Face API configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not HUGGINGFACE_API_KEY:
    raise ValueError("HUGGINGFACE_API_KEY not found in environment variables")

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

# Cache for API responses
api_cache = {}

@lru_cache(maxsize=1)
def load_tag_hierarchy():
    with open("tag_hierarchy.json", "r") as f:
        return json.load(f)

def batch(iterable, size):
    """Split an iterable into batches of specified size."""
    iterator = iter(iterable)
    while batch := list(islice(iterator, size)):
        yield batch

def get_relevant_asset_tags(description: str) -> List[str]:
    """Get only the most relevant tags based on the description."""
    tag_hierarchy = load_tag_hierarchy()
    relevant_tags = []
    description_lower = description.lower()
    
    # Add asset type tags
    asset_types = {
        'baseplate': ['baseplate', 'base plate', 'base-plate'],
        'dealer-logo': ['dealer logo', 'dealerlogos', 'dealer-logos'],
        'award-logo': ['award logo', 'awardlogos', 'award-logos', 'award'],
        'energy-label': ['energy label', 'energylabel', 'energy-label'],
        'car-logo': ['car logo', 'carlogo', 'car-logos', 'brand logo', 'brandlogos'],
        'qr-code': ['qr', 'qr-code', 'qrcode', 'qr code'],
        'social-logo': ['social logo', 'sociallogos', 'social-logos', 'social media logo'],
        'warranty-logo': ['warranty logo', 'warrantylogos', 'warranty-logos', 'warranty'],
        'packshot': ['packshot', 'packshots', 'pack shot', 'pack-shot'],
        'additional-logo': ['additional logo', 'additionallogos', 'additional-logos'],
        'customer-promise': ['customer promise', 'customerpromise', 'customer-promise']
    }
    
    # Check for each asset type
    for asset_type, keywords in asset_types.items():
        if any(keyword in description_lower for keyword in keywords):
            relevant_tags.append(f"type/{asset_type}")
            break  # Only add the first matching asset type
    
    # Add language tags
    if any(lang in description_lower for lang in ['finnish', 'suomi', 'fi']):
        relevant_tags.append("language/finnish")
    elif any(lang in description_lower for lang in ['swedish', 'ruotsi', 'sv']):
        relevant_tags.append("language/swedish")
    elif any(lang in description_lower for lang in ['norwegian', 'norja', 'no']):
        relevant_tags.append("language/norwegian")
    elif any(lang in description_lower for lang in ['danish', 'tanska', 'dk']):
        relevant_tags.append("language/danish")
    elif any(lang in description_lower for lang in ['estonian', 'viro', 'et']):
        relevant_tags.append("language/estonian")
    elif any(lang in description_lower for lang in ['latvian', 'latvia', 'lv']):
        relevant_tags.append("language/latvian")
    elif any(lang in description_lower for lang in ['lithuanian', 'liettua', 'lt']):
        relevant_tags.append("language/lithuanian")
    elif any(lang in description_lower for lang in ['russian', 'venäjä', 'ru']):
        relevant_tags.append("language/russian")
    else:
        relevant_tags.append("language/english")  # Default to English if no language is detected
    
    # Add vehicle filter tags if present
    vehicle_models = tag_hierarchy['filter']['subcategories']['vehicle']
    for model in vehicle_models:
        model_lower = model.lower()
        if model_lower in description_lower:
            relevant_tags.append(f"filter/vehicle/{model}")
            break
    
    return relevant_tags

def suggest_asset_tags(description: str) -> Dict:
    """Suggest tags for assets based on the description."""
    tag_hierarchy = load_tag_hierarchy()
    description_lower = description.lower()
    suggestions = []
    
    try:
        # Get relevant tags based on description
        relevant_tags = get_relevant_asset_tags(description)
        
        # Always add system/origin/aws tag
        relevant_tags.append("system/origin/aws")
        
        # Create suggestions based on tag categories
        tag_categories = {
            "type": [],
            "language": [],
            "filter": [],
            "system": []
        }
        
        # Categorize tags
        for tag in relevant_tags:
            category = tag.split('/')[0]
            if category in tag_categories:
                tag_categories[category].append(tag)
        
        # Create suggestion objects for each category
        for category, tags in tag_categories.items():
            if tags:
                suggestions.append({
                    "category": category,
                    "suggested_tags": tags,
                    "confidence": 0.95  # High confidence for asset tags
                })
        
        return {"suggestions": suggestions}
            
    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__
        print(f"Error getting asset suggestions: {error_message}")
        print(f"Error type: {error_type}")
        
        # Create a fallback response
        fallback_suggestions = {
            "suggestions": [
                {
                    "category": "type",
                    "suggested_tags": ["type/image"],
                    "confidence": 0.95
                },
                {
                    "category": "language",
                    "suggested_tags": ["language/english"],
                    "confidence": 0.90
                },
                {
                    "category": "system",
                    "suggested_tags": ["system/origin/aws"],
                    "confidence": 1.0
                }
            ],
            "is_fallback": True,
            "error": {
                "message": error_message,
                "type": error_type
            }
        }
        
        print("Using fallback suggestions due to API error")
        return fallback_suggestions 