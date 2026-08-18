from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Import modules locally to avoid import-time side-effects (fast startup)
from backend.ai_service import analyze_reel_with_gemini, explain_recommendation_with_gemini
from backend.fallback_engine import analyze_locally
from backend.recommender import get_recommendations

# Load environment variables
load_dotenv()

app = FastAPI(title="TechScroll AI - Hackathon Build")

class RecommendRequest(BaseModel):
    description: str
    caption: str

def generate_local_explanation(profile: dict, recommended_reel: dict, current_reel: dict) -> str:
    """
    Generates a high-quality deterministic explanation if Gemini is offline or unavailable.
    """
    category = recommended_reel.get("category", "")
    interest = profile.get("primary_interest", "")
    
    if category == "DSA":
        return f"Your scrolling indicates an interest in {interest}. Rather than focusing on narrow language features, we recommend preparing coding interview patterns and data structures to build core software engineering competence."
    elif category == "AI":
        return f"We detected a strong interest in Artificial Intelligence. This recommendation introduces foundational architectures (like agents, transformer mechanisms, and memory layers) to help you understand the future of generative models."
    elif category == "Cybersecurity":
        return f"In response to your interest in cybersecurity, this Reel details practical mitigation strategies and security fundamentals like authentication and SQL injection prevention."
    elif category == "Cloud":
        return f"This recommendation bridges your backend interest with scalable cloud practices, explaining containerization, infrastructure, and distributed database scaling concepts."
    elif category == "Hardware":
        return f"We mapped your interest to Hardware / Computer Technology. This recommended video explains GPU and CPU differences or architecture choices that help developers write optimized programs."
    elif category == "HLD":
        return f"To support your interest in software architecture, we recommend this High-Level Design guide, illustrating scaling patterns and architectural trade-offs."
    elif category == "Java":
        return f"Since you showed interest in Java, this Reel helps you go deeper into Java's runtime memory management and performance optimizations."
    else:
        return f"This recommended tech Reel on {category} connects your interest in {interest} with actionable, high-quality educational insights to make your scrolling time more productive."

def generate_interest_path(primary_interest: str, current_reel: dict, rec_title: str) -> list[str]:
    """
    Generates a dynamic visual path showing how the interest was derived.
    """
    desc = (current_reel.get("description", "") + " " + current_reel.get("caption", "")).lower()
    
    # 1. Identify starting seed keyword
    seed = "Code"
    if "java" in desc:
        seed = "Java"
    elif "llm" in desc or "agent" in desc or "ai" in desc:
        seed = "LLM/AI"
    elif "phishing" in desc or "password" in desc or "credential" in desc or "hack" in desc:
        seed = "Phishing"
    elif "cpu" in desc or "gpu" in desc or "laptop" in desc or "processor" in desc:
        seed = "CPU/GPU"
    elif "aws" in desc or "cloud" in desc or "docker" in desc or "kubernetes" in desc:
        seed = "Cloud"
    elif "binary" in desc or "algorithm" in desc or "list" in desc or "dsa" in desc:
        seed = "Algorithms"
        
    steps = [seed]
    
    # Add intermediate steps dynamically based on interest
    interest_lower = primary_interest.lower()
    if "software engineering" in interest_lower or "programming" in interest_lower:
        steps.extend(["Programming", "Debugging", "Software Development"])
    elif "artificial intelligence" in interest_lower or "ai" in interest_lower:
        steps.extend(["Machine Learning", "Neural Networks", "Generative AI"])
    elif "cybersecurity" in interest_lower or "security" in interest_lower:
        steps.extend(["Social Engineering", "Attack Vectors", "Network Security"])
    elif "hardware" in interest_lower or "computer technology" in interest_lower:
        steps.extend(["Processor Layout", "Specs", "System Performance"])
    elif "cloud" in interest_lower:
        steps.extend(["Containers", "Deployment", "Infrastructure"])
    elif "dsa" in interest_lower:
        steps.extend(["Data Structures", "Complexity", "Algorithms"])
    else:
        steps.extend(["Syntax", "Concepts", "Tech Topics"])
        
    steps.append(primary_interest)
    
    # Append short title
    short_title = rec_title
    if len(short_title) > 25:
        short_title = short_title[:22] + "..."
    steps.append(short_title)
    
    return steps

@app.get("/")
def get_index():
    """Serves the frontend single-page interface."""
    return FileResponse("frontend/index.html")

@app.get("/style.css")
def get_style():
    """Serves the CSS stylesheet."""
    return FileResponse("frontend/style.css")

@app.get("/app.js")
def get_app():
    """Serves the frontend JavaScript script."""
    return FileResponse("frontend/app.js")

@app.get("/api/health")
def health_check():
    """Health check endpoint for status and debugging."""
    return {"status": "ok"}

@app.post("/api/recommend")
def recommend(request: RecommendRequest):
    """
    Main recommendation endpoint. Analyzes user inputs and ranks the candidates.
    """
    desc = request.description.strip()
    cap = request.caption.strip()
    
    if not desc and not cap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a Reel description or caption."
        )
        
    try:
        # 1. Content Understanding & Interest Inference
        mode = "gemini"
        profile = analyze_reel_with_gemini(desc, cap)
        
        # If API Key is missing or invalid or call failed, fall back to local rule engine
        if not profile:
            profile = analyze_locally(desc, cap)
            mode = "fallback"
            
        # 2. Python Recommendation Engine (Scoring and ranking candidates)
        recs = get_recommendations(profile, {"description": desc, "caption": cap})
        rec_reel = recs["recommended_tech_reel"]
        
        # 3. Generate Explanation
        explanation = None
        if mode == "gemini":
            explanation = explain_recommendation_with_gemini(profile, rec_reel, {"description": desc, "caption": cap})
            
        if not explanation:
            explanation = generate_local_explanation(profile, rec_reel, {"description": desc, "caption": cap})
            
        # 4. Formulate response
        return {
            "current_reel": {
                "description": desc,
                "caption": cap
            },
            "interest_detected": {
                "topic": profile["primary_interest"],
                "confidence": profile["confidence"]
            },
            "why": profile["evidence"],
            "recommended_tech_reel": {
                "title": rec_reel["title"],
                "category": rec_reel["category"],
                "difficulty": rec_reel["difficulty"]
            },
            "category": rec_reel["category"],
            "why_this_recommendation": explanation,
            "difficulty": rec_reel["difficulty"],
            "confidence": profile["confidence"],
            "why_not": recs["why_not"],
            "score_breakdown": recs["score_breakdown"],
            "interest_path": generate_interest_path(profile["primary_interest"], {"description": desc, "caption": cap}, rec_reel["title"]),
            "mode": mode
        }
    except Exception as e:
        # Never expose raw stack traces in responses for security
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing recommendations: {str(e)}"
        )
