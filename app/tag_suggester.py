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

print(f"Using Hugging Face API key: {HUGGINGFACE_API_KEY[:8]}...")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

# Cache for API responses
api_cache = {}

@lru_cache(maxsize=1)
def load_tag_hierarchy():
    with open("tag_hierarchy.json", "r") as f:
        return json.load(f)

@lru_cache(maxsize=1)
def load_car_models():
    try:
        with open("../car_models.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: car_models.json not found. Using empty car models list.")
        return {}

def batch(iterable, size):
    """Split an iterable into batches of specified size."""
    iterator = iter(iterable)
    while batch := list(islice(iterator, size)):
        yield batch

def get_relevant_tags(description: str) -> List[str]:
    """Get only the most relevant tags based on the description."""
    tag_hierarchy = load_tag_hierarchy()
    relevant_tags = []
    description_lower = description.lower()
    
    # Add vehicle tags
    vehicles = ['qashqai', 'juke', 'x-trail', 'leaf', 'micra', 'ariya']
    for vehicle in vehicles:
        if vehicle in description_lower:
            relevant_tags.append(f"filter/vehicle/{vehicle}")
            break  # Only add the first matching vehicle
    
    # Add language tags
    if any(lang in description_lower for lang in ['finnish', 'swedish', 'norwegian', 'danish', 'estonian', 'latvian', 'lithuanian', 'russian', 'english']):
        relevant_tags.extend([f"language/{lang}" for lang in ['finnish', 'swedish', 'norwegian', 'danish', 'estonian', 'latvian', 'lithuanian', 'russian', 'english']])
    
    # Add media type tags
    if any(media in description_lower for media in ['print', 'banner', 'edm', 'dm', 'pricelectern', 'pos', 'digiscreen']):
        relevant_tags.extend([f"system/media/{media}" for media in ['print', 'banner', 'edm', 'dm', 'pricelectern', 'pos', 'digiscreen']])
    
    return relevant_tags

def suggest_tags(description: str) -> Dict:
    tag_hierarchy = load_tag_hierarchy()
    car_models = load_car_models()
    description_lower = description.lower()
    suggestions = []
    
    print("\n=== Starting tag suggestion process ===")
    print(f"Input description: {description}")
    
    try:
        # Try to make API call but don't let it block our keyword matching
        try:
            # Get only relevant tags for API call
            relevant_tags = get_relevant_tags(description)
            
            # Check cache first
            cache_key = f"{description}_{','.join(sorted(relevant_tags))}"
            if cache_key in api_cache:
                combined_labels = api_cache[cache_key]['labels']
                combined_scores = api_cache[cache_key]['scores']
            else:
                # Prepare the request for zero-shot classification
                headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
                
                # Process tags in batches of 10 (model limitation)
                all_results = []
                for tag_batch in batch(relevant_tags, 10):
                    payload = {
                        "inputs": description,
                        "parameters": {
                            "candidate_labels": tag_batch,
                            "multi_label": True
                        }
                    }
                    
                    # Make the API call with a shorter timeout
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        result = response.json()
                        all_results.append(result)
                    else:
                        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
                
                # Combine results from all batches
                combined_labels = []
                combined_scores = []
                for result in all_results:
                    combined_labels.extend(result.get('labels', []))
                    combined_scores.extend(result.get('scores', []))
                
                # Cache the results
                api_cache[cache_key] = {
                    'labels': combined_labels,
                    'scores': combined_scores,
                    'timestamp': time.time()
                }
                
                # Clean up old cache entries (older than 1 hour)
                current_time = time.time()
                api_cache.clear()  # Simple cache clearing for now
            
        except Exception as api_error:
            print(f"\nAPI error: {str(api_error)}")
            print("Proceeding with keyword matching only")
            combined_labels = []
            combined_scores = []
        
        # Define media type to size relationships
        media_size_relationships = {
            'print': {
                'valid_sizes': ['fullpage', 'halfpage', 'quarterpage'],
                'keywords': ['print', 'printer', 'printed', 'printing'],
                'comment': 'Print media has three possible sizes'
            },
            'html5-banner': {
                'valid_sizes': ['static'],
                'keywords': ['banner', 'banners', 'html5', 'html5-banner'],
                'comment': 'HTML5 banners have one fixed size'
            },
            'edm': {
                'valid_sizes': [],
                'keywords': ['edm', 'email', 'newsletter'],
                'comment': 'Email doesn\'t have sizes'
            },
            'dm': {
                'valid_sizes': ['dm'],
                'keywords': ['dm', 'direct media', 'direct mail'],
                'comment': 'Direct media has one fixed size'
            },
            'pricelectern': {
                'valid_sizes': ['a4'],
                'keywords': ['price lectern', 'pricelectern', 'price-lectern'],
                'comment': 'Price lectern has fixed A4 size'
            },
            'pos': {
                'valid_sizes': [],
                'keywords': ['pos', 'point of sale', 'point-of-sale'],
                'comment': 'POS has fixed size'
            },
            'digiscreen': {
                'valid_sizes': [],
                'keywords': ['digiscreen', 'digital screen', 'digital-screen'],
                'comment': 'Digital screen has fixed size'
            },
            'socialmedia': {
                'valid_sizes': ['linkad', 'story'],
                'keywords': ['social media', 'social', 'socialmedia', 'instagram', 'facebook', 'linkedin', 'social network', 'social networks'],
                'comment': 'Social media has two possible sizes: linkad and story'
            },
            'aftersales': {
                'valid_sizes': [],
                'keywords': ['after sales', 'aftersales', 'after-sales'],
                'comment': 'After sales has fixed size'
            },
            'A4_leaflet': {
                'valid_sizes': [],
                'keywords': ['a4 leaflet', 'a4-leaflet', 'leaflet', 'a4'],
                'comment': 'A4 leaflet has fixed size'
            },
            'aftersales/socialmedia': {
                'valid_sizes': ['linkad', 'story'],
                'keywords': ['after sales social', 'aftersales social', 'after-sales social', 'after sales social media', 'aftersales social media'],
                'comment': 'After sales social media has two possible sizes: linkad and story'
            }
        }
        
        # Define size keywords
        size_keywords = {
            'fullpage': ['full page', 'fullpage', 'full-page'],
            'halfpage': ['half page', 'halfpage', 'half-page'],
            'quarterpage': ['quarter page', 'quarterpage', 'quarter-page'],
            'dm': ['dm', 'direct media', 'direct mail'],
            'linkad': ['linkad', 'linkedin ad', 'linkedin advertisement', 'linkedin post'],
            'story': ['story', 'instagram story', 'facebook story', 'social story', 'stories', 'instagram stories', 'facebook stories'],
            'static': ['static', 'html5', 'html5-banner'],
            'a4': ['a4', 'a4-size', 'a4 size']
        }
        
        # Define required categories and their keywords
        required_categories = {
            'filter': {
                'keywords': {
                    'vehicle': {
                        'ariya': ['ariya', 'ariya-model', 'ariya-ev'],
                        'qashqai': ['qashqai', 'qashqai-model', 'qq', 'qash'],
                        'juke': ['juke', 'juke-model', 'juke-ev'],
                        'leaf': ['leaf', 'leaf-model', 'leaf-ev'],
                        'micra': ['micra', 'micra-model'],
                        'x-trail': ['x-trail', 'xtrail', 'xt'],
                        'env200': ['env200', 'env200-model', 'env'],
                        'gt-r': ['gt-r', 'gtr', 'gtr-model', 'gtr35'],
                        'navara': ['navara', 'navara-model', 'nav'],
                        'primastar': ['primastar', 'primastar-model', 'prim'],
                        'interstar': ['interstar', 'interstar-model', 'inter'],
                        'townstar': ['townstar', 'townstar-model', 'town'],
                        'nv250': ['nv250', 'nv250-model', 'nv2'],
                        'nv400': ['nv400', 'nv400-model', 'nv4'],
                        'crosscarline': ['crosscarline', 'cross-carline', 'ccl'],
                        'interstar2024': ['interstar2024', 'interstar-2024', 'inter24']
                    },
                    'lcv': {
                        'env200': ['env200', 'env200-model', 'env200-van', 'env200-evalia', 'env', 'env2'],
                        'nv200': ['nv200', 'nv200-model', 'nv2'],
                        'navara': ['navara', 'navara-model', 'nav'],
                        'nv400': ['nv400', 'nv400-model', 'nv4'],
                        'nv300': ['nv300', 'nv300-model', 'nv3'],
                        'nt400': ['nt400', 'nt400-model', 'nt4'],
                        'nv250': ['nv250', 'nv250-model', 'nv2'],
                        'primastar': ['primastar', 'primastar-model', 'prim'],
                        'interstar': ['interstar', 'interstar-model', 'inter'],
                        'townstar': ['townstar', 'townstar-model', 'town', 'ets']
                    },
                    'fleet': {
                        'qashqai': ['qashqai', 'qashqai-model', 'qq', 'qash'],
                        'x-trail': ['x-trail', 'xtrail', 'xt'],
                        'leaf': ['leaf', 'leaf-model', 'leaf-ev']
                    }
                },
                'default': 'filter/vehicle/qashqai'
            },
            'system/media': {
                'keywords': media_size_relationships,
                'default': 'system/media/print'
            },
            'system/size': {
                'keywords': size_keywords,
                'default': None  # No default size
            },
            'language': {
                'keywords': {
                    'finnish': ['finnish', 'suomi', 'suomenkielinen', 'fi', 'fin', 'finn'],
                    'swedish': ['swedish', 'ruotsi', 'ruotsinkielinen', 'sv', 'swe', 'swed'],
                    'norwegian': ['norwegian', 'norja', 'norjankielinen', 'no', 'nor', 'norw'],
                    'danish': ['danish', 'tanska', 'tanskankielinen', 'dk', 'dan', 'dane'],
                    'estonian': ['estonian', 'viro', 'viroinkielinen', 'et', 'est', 'eston'],
                    'latvian': ['latvian', 'latvia', 'latviankielinen', 'lv', 'lav', 'latv'],
                    'lithuanian': ['lithuanian', 'liettua', 'liettuan', 'lt', 'lit', 'lith'],
                    'russian': ['russian', 'venäjä', 'venäjän', 'ru', 'rus', 'russ'],
                    'english': ['english', 'englanti', 'englanninkielinen', 'en', 'eng', 'engl']
                },
                'default': None  # No default language
            }
        }
        
        # First, determine the media type
        detected_media_type = None
        
        # Check for social media specific keywords first
        social_media_keywords = ['linkad', 'story', 'stories', 'instagram', 'facebook', 'linkedin', 'post']
        if any(keyword in description_lower for keyword in social_media_keywords):
            detected_media_type = 'socialmedia'
        else:
            # If no social media keywords found, check other media types
            for media_type, config in media_size_relationships.items():
                if any(keyword in description_lower for keyword in config['keywords']):
                    detected_media_type = media_type
                    break
        
        # Process each required category
        for category, config in required_categories.items():
            category_suggestions = []
            
            if category == 'language':
                # Check for language keywords in the description
                detected_language = None
                for lang, keywords in config['keywords'].items():
                    if any(f" {keyword} " in f" {description_lower} " for keyword in keywords):
                        detected_language = lang
                        break
                
                # If a language was detected, only suggest that language
                if detected_language:
                    category_suggestions.append({
                        "tag": f"language/{detected_language}",
                        "confidence": 0.9
                    })
                else:
                    # If no language was detected, suggest all available languages
                    for lang in config['keywords'].keys():
                        category_suggestions.append({
                            "tag": f"language/{lang}",
                            "confidence": 0.5
                        })
            elif category == 'filter':
                # Special handling for vehicle categories
                # First try direct tag matching from API results if available
                if combined_labels:
                    for subcategory, models in config['keywords'].items():
                        if subcategory == 'vehicle':  # Only check vehicle category
                            for model, keywords in models.items():
                                # Check if the model is in the combined labels
                                if any(model.lower() in label.lower() for label in combined_labels):
                                    idx = next(i for i, label in enumerate(combined_labels) if model.lower() in label.lower())
                                    confidence = combined_scores[idx]
                                    if confidence > 0.5:
                                        category_suggestions.append({
                                            "tag": f"filter/{subcategory}/{model}",
                                            "confidence": confidence
                                        })
                                        break
                
                # If no direct matches or no API results, try keyword matching
                if not category_suggestions:
                    # Check each vehicle category
                    for subcategory, models in config['keywords'].items():
                        if subcategory == 'vehicle':  # Only check vehicle category
                            for model, keywords in models.items():
                                if any(keyword in description_lower for keyword in keywords):
                                    category_suggestions.append({
                                        "tag": f"filter/{subcategory}/{model}",
                                        "confidence": 0.9
                                    })
                                    break
                            if category_suggestions:
                                break
            elif category == 'system/media':
                # Special handling for media types
                if detected_media_type:
                    category_suggestions.append({
                        "tag": f"system/media/{detected_media_type}",
                        "confidence": 0.9
                    })
                else:
                    # If no media type detected, suggest all media options with lower confidence
                    for media_type in media_size_relationships.keys():
                        category_suggestions.append({
                            "tag": f"system/media/{media_type}",
                            "confidence": 0.5
                        })
            elif category == 'system/size':
                # Special handling for size based on detected media type
                if detected_media_type:
                    # If we have a detected media type, only suggest its valid sizes
                    media_config = media_size_relationships[detected_media_type]
                    valid_system_sizes = media_config['valid_sizes']
                    
                    if valid_system_sizes:
                        # Try to match specific system size from description
                        for size, keywords in size_keywords.items():
                            if size in valid_system_sizes and any(keyword in description_lower for keyword in keywords):
                                category_suggestions.append({
                                    "tag": f"system/size/{size}",
                                    "confidence": 0.9
                                })
                                break
                        
                        # If no specific size matched, suggest all valid system sizes
                        if not category_suggestions:
                            for size in valid_system_sizes:
                                category_suggestions.append({
                                    "tag": f"system/size/{size}",
                                    "confidence": 0.5
                                })
                else:
                    # If no media type detected, suggest all system sizes
                    for size in size_keywords.keys():
                        category_suggestions.append({
                            "tag": f"system/size/{size}",
                            "confidence": 0.5
                        })
            
            # If still no suggestions, provide all available options for the category
            if not category_suggestions:
                if category == 'system/size':
                    # Add all system size options with lower confidence
                    for size in size_keywords.keys():
                        category_suggestions.append({
                            "tag": f"system/size/{size}",
                            "confidence": 0.5
                        })
                elif category == 'system/media':
                    # Add all media options with lower confidence
                    for media_type in media_size_relationships.keys():
                        category_suggestions.append({
                            "tag": f"system/media/{media_type}",
                            "confidence": 0.5
                        })
                elif category == 'filter':
                    # Add all vehicle options with lower confidence
                    for subcategory, models in config['keywords'].items():
                        for model in models.keys():
                            category_suggestions.append({
                                "tag": f"filter/{subcategory}/{model}",
                                "confidence": 0.5
                            })
                elif category == 'language':
                    # Add all language options with lower confidence
                    for lang in config['keywords'].keys():
                        category_suggestions.append({
                            "tag": f"language/{lang}",
                            "confidence": 0.5
                        })
            
            # Add the best suggestion to the results
            suggestions.append({
                "category": category,
                "suggested_tags": [s['tag'] for s in category_suggestions],
                "confidence": category_suggestions[0]['confidence'] if category_suggestions else 0.5
            })
        
        # Add banner size suggestions if banner media type is detected
        if detected_media_type == 'html5-banner':
            suggestions.append({
                "category": "banner/size",
                "suggested_tags": ["banner/size/<width>x<height>"],
                "confidence": 0.5
            })
        
        # Add car model suggestions for price lecterns
        if detected_media_type == 'pricelectern':
            # Find the detected car model from filter suggestions
            detected_model = None
            for suggestion in suggestions:
                if suggestion['category'] == 'filter' and any('filter/vehicle/' in tag for tag in suggestion['suggested_tags']):
                    detected_model = suggestion['suggested_tags'][0].split('/')[-1]
                    break
            
            if detected_model:
                # Check if the model exists in the car models list
                if detected_model in car_models:
                    model_info = car_models[detected_model]
                    # Add base model tag
                    model_tags = [f"car/model/{detected_model}"]
                    # Add year-specific tags
                    for year in model_info['years']:
                        model_tags.append(f"car/model/{detected_model}/{year}")
                    suggestions.append({
                        "category": "car/model",
                        "suggested_tags": model_tags,
                        "confidence": 0.9,
                        "conditional_tags": {
                            "system/dynamic/text": {
                                "description": {
                                    "finnish": "Tämä lisätagi mahdollistaa hintalistatietokannan käytön tämän mallin käyttäjille",
                                    "swedish": "Denna ytterligare tagg möjliggör användning av prislistdatabasen för användare av denna mall",
                                    "norwegian": "Denne ekstra taggen muliggjør bruk av prislistedatabasen for brukere av denne malen",
                                    "danish": "Denne ekstra tag muliggør brug af prislistedatabasen for brugere af denne skabelon",
                                    "estonian": "See lisatag võimaldab selle malli kasutajatel kasutada hinnakirja andmebaasi",
                                    "latvian": "Šis papildu tags ļauj šī veidnes lietotājiem izmantot cenu saraksta datubāzi",
                                    "lithuanian": "Šis papildomas žymėjimas leidžia šio šablono vartotojams naudoti kainų sąrašo duomenų bazę",
                                    "russian": "Этот дополнительный тег позволяет пользователям этого шаблона использовать базу данных прайс-листа",
                                    "english": "This additional tag enables the price lectern database for the users of this template"
                                },
                                "trigger_tags": [f"car/model/{detected_model}"] + [f"car/model/{detected_model}/{year}" for year in model_info['years']]
                            }
                        }
                    })
        
        return {"suggestions": suggestions}
            
    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__
        print(f"Error getting suggestions: {error_message}")
        print(f"Error type: {error_type}")
        
        # Create a more informative fallback response
        fallback_suggestions = {
            "suggestions": [
                {
                    "category": "filter",
                    "suggested_tags": ["filter/vehicle/qashqai"],
                    "confidence": 0.95
                },
                {
                    "category": "system/media",
                    "suggested_tags": ["system/media/print"],
                    "confidence": 0.85
                },
                {
                    "category": "system/size",
                    "suggested_tags": ["system/size/halfpage"],
                    "confidence": 0.80
                },
                {
                    "category": "language",
                    "suggested_tags": ["language/finnish"],
                    "confidence": 0.90
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

def parse_filename(filename: str) -> Dict:
    """Parse a filename according to the naming convention and extract relevant information."""
    # Remove file extension if present
    filename = filename.split('.')[0]
    
    # Initialize result dictionary
    result = {
        'fiscal_year': None,
        'quarter': None,
        'project_type': None,
        'language': None,
        'vehicles': [],
        'media_type': None,
        'dimensions': None,
        'version': None
    }
    
    # Split by underscore or space
    parts = filename.replace(' ', '_').split('_')
    
    # Parse fiscal year and quarter
    if parts[0].startswith('FY'):
        result['fiscal_year'] = parts[0]
        if '_' in parts[0]:
            fy_parts = parts[0].split('_')
            result['fiscal_year'] = fy_parts[0]
            result['quarter'] = fy_parts[1]
        else:
            result['quarter'] = parts[1]
            parts = parts[1:]  # Remove the quarter part as it's already processed
    
    # Parse project type
    if parts[1] in ['CCL', 'MASTER']:
        result['project_type'] = parts[1]
        parts = parts[1:]
    
    # Parse language
    language_map = {
        'FIN': 'finnish',
        'NOR': 'norwegian',
        'SWE': 'swedish',
        'DAN': 'danish',
        'EST': 'estonian',
        'LAT': 'latvian',
        'LIT': 'lithuanian',
        'RUS': 'russian',
        'ENG': 'english'
    }
    
    if parts[1] in language_map:
        result['language'] = language_map[parts[1]]
        parts = parts[1:]
    
    # Parse vehicles (there might be multiple)
    vehicle_index = 1
    while vehicle_index < len(parts) and parts[vehicle_index] not in ['STORY', 'BANNER', 'PRINT']:
        result['vehicles'].append(parts[vehicle_index].replace('QASHQAL', 'QASHQAI'))  # Fix common typo
        vehicle_index += 1
    
    # Parse media type and dimensions
    for i in range(vehicle_index, len(parts)):
        if parts[i] in ['STORY', 'BANNER', 'PRINT']:
            result['media_type'] = parts[i].lower()
        elif 'x' in parts[i].lower():
            result['dimensions'] = parts[i]
        elif parts[i].startswith('V') or parts[i].isdigit():
            result['version'] = parts[i]
    
    return result

def suggest_tags_from_filename(filename: str) -> Dict:
    """Suggest tags based on a filename."""
    parsed = parse_filename(filename)
    suggestions = []
    
    # Add language tag
    if parsed['language']:
        suggestions.append({
            "category": "language",
            "suggested_tags": [f"language/{parsed['language']}"],
            "confidence": 1.0
        })
    
    # Add vehicle tags
    if parsed['vehicles']:
        suggestions.append({
            "category": "filter",
            "suggested_tags": [f"filter/vehicle/{vehicle}" for vehicle in parsed['vehicles']],
            "confidence": 1.0
        })
    
    # Add media type tag
    if parsed['media_type']:
        suggestions.append({
            "category": "system/media",
            "suggested_tags": [f"system/media/{parsed['media_type']}"],
            "confidence": 1.0
        })
    
    # Add size tag for banners
    if parsed['dimensions'] and parsed['media_type'] == 'banner':
        width, height = parsed['dimensions'].split('x')
        suggestions.append({
            "category": "banner/size",
            "suggested_tags": [f"banner/size/{width}x{height}"],
            "confidence": 1.0
        })
    
    return {"suggestions": suggestions} 