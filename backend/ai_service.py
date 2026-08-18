import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class InterestProfile(BaseModel):
    primary_interest: str = Field(description="The inferred broad technology interest (e.g. Software Engineering, Artificial Intelligence, Cybersecurity, Hardware, Cloud, etc.)")
    confidence: str = Field(description="Confidence level: High, Medium, or Low")
    interest_strength: int = Field(description="Strength of interest from 0 to 100")
    evidence: List[str] = Field(description="List of specific evidences/clues from the description or caption explaining this classification")
    related_interests: List[str] = Field(description="2-4 related interests or sub-categories")

def analyze_reel_with_gemini(description: str, caption: str) -> Optional[dict]:
    """
    Calls the Gemini API to analyze the Reel description and caption,
    returning a structured interest profile.
    Initializes the client inside the function call to prevent import-time side-effects.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
        
    try:
        # Initialize client here to avoid startup API calls or loading keys at import
        client = genai.Client(api_key=api_key)
        
        prompt = f"""You are an AI recommendation analyst.

Analyze the provided short-form Reel description and caption.

Your task is NOT to simply identify keywords.
Infer the broader underlying technology interest represented by the content.

Consider:
- semantic meaning
- context
- apparent interest
- related concepts
- professional relevance

For example, a Java meme combined with developer context should indicate Software Engineering or Programming rather than only Java.

Reel Description: "{description}"
Reel Caption: "{caption}"

IMPORTANT: For the "evidence" field, DO NOT output keyword detection strings like "Contains Java keyword" or "Detected developer". 
Instead, output high-quality semantic and contextual evidence statements, such as:
- "The Reel focuses on software development and debugging."
- "The debugging context indicates interest in solving programming problems."
- "The developer context suggests broader software-engineering interest."
- "The content is not limited to specific syntax or language-specific learning."

Return valid JSON according to the schema. Do not recommend a Reel yet."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InterestProfile,
            ),
        )
        
        # Parse the JSON response
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Gemini API failure during content understanding: {e}")
        return None

def explain_recommendation_with_gemini(profile: dict, recommended_reel: dict, current_reel: dict) -> Optional[str]:
    """
    Uses Gemini to generate a short explanation of why the candidate was recommended
    based on the inferred interest profile and current Reel.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""You are an AI recommendation analyst.
Explain why we are recommending the technology Reel: "{recommended_reel['title']}" (Category: {recommended_reel['category']}) to a student who just watched a Reel with description: "{current_reel['description']}" and caption: "{current_reel['caption']}".

The system inferred their broader interest as: "{profile['primary_interest']}".
Explain the connection in exactly 2 to 4 sentences.
Do NOT change the recommended Reel, do NOT suggest other candidates, and keep the tone professional and educational.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API failure during explanation generation: {e}")
        return None
