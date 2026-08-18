import os
import json
import re
from typing import List, Tuple, Dict

# Map broad interest profiles to relevant candidate categories
BROAD_INTEREST_MAPPING = {
    "Software Engineering / Programming": ["DSA", "Programming", "Career", "HLD", "Java"],
    "Software Engineering": ["DSA", "Programming", "Career", "HLD", "Java"],
    "Programming": ["DSA", "Programming", "Career", "HLD", "Java"],
    "Artificial Intelligence": ["AI", "Technology News"],
    "Cybersecurity": ["Cybersecurity"],
    "Hardware / Computer Technology": ["Hardware", "Technology News"],
    "Hardware": ["Hardware", "Technology News"],
    "Cloud": ["Cloud", "HLD"],
    "Cloud / Backend Engineering": ["Cloud", "HLD"],
    "DSA / Software Engineering": ["DSA", "Programming", "Career"]
}

HYPE_PHRASES = [
    "guaranteed", "guarantee", "get rich", "secret", "7 days", "instant",
    "replace your career", "guaranteed job", "one tool", "overnight success",
    "make $", "replace software developers", "earn $", "weekend", "one weekend"
]

def load_candidates() -> List[dict]:
    """
    Loads candidate Reels from candidate_reels.json.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "candidate_reels.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading candidates from {file_path}: {e}")
        return []

def calculate_score(candidate: dict, profile: dict, current_reel: dict) -> Tuple[float, Dict[str, float], float, float]:
    """
    Calculates the final recommendation score and breakdown for a candidate.
    """
    primary_interest = profile.get("primary_interest", "")
    related_interests = profile.get("related_interests", [])
    
    # 1. Interest Match (Max 40 points)
    interest_match_score = 0.0
    
    # Check if category matches direct mappings
    matched_categories = BROAD_INTEREST_MAPPING.get(primary_interest, [])
    # Case-insensitive category match
    cand_category = candidate.get("category", "")
    
    if cand_category.lower() in [c.lower() for c in matched_categories]:
        interest_match_score = 40.0
    else:
        # Check topic overlap with primary and related interests
        cand_topics = [t.lower() for t in candidate.get("topics", [])]
        overlap_count = 0
        all_interests = [primary_interest.lower()] + [r.lower() for r in related_interests]
        
        for topic in cand_topics:
            for interest in all_interests:
                if topic in interest or interest in topic:
                    overlap_count += 1
                    
        if overlap_count >= 2:
            interest_match_score = 30.0
        elif overlap_count >= 1:
            interest_match_score = 20.0
        else:
            # Basic text similarity check
            combined_text = (candidate.get("title", "") + " " + candidate.get("description", "")).lower()
            if any(term in combined_text for term in all_interests):
                interest_match_score = 15.0
            else:
                interest_match_score = 5.0
                
    # 2. Educational Value (Max 25 points - 25% of 0-100)
    edu_value = candidate.get("educational_value", 0) * 0.25
    
    # 3. Career Relevance (Max 15 points - 15% of 0-100)
    career_relevance = candidate.get("career_relevance", 0) * 0.15
    
    # 4. Engagement Potential (Max 10 points - 10% of 0-100)
    engagement = candidate.get("engagement_potential", 0) * 0.10
    
    # 5. Hype Penalty
    hype_penalty = 0.0
    hype_prob = candidate.get("hype_probability", 0)
    if hype_prob > 15:
        # Add penalty proportional to hype probability
        hype_penalty += hype_prob * 0.3
        
    # Check for hype phrases in title and description
    title_desc = (candidate.get("title", "") + " " + candidate.get("description", "")).lower()
    for phrase in HYPE_PHRASES:
        if phrase in title_desc:
            hype_penalty += 30.0
            break
            
    # Cap hype penalty to fit UI / scoring design, but make it significant
    hype_penalty = min(hype_penalty, 50.0)
    
    # 6. Repetition/Narrowness Penalty
    repetition_penalty = 0.0
    curr_text = (current_reel.get("description", "") + " " + current_reel.get("caption", "")).lower()
    
    cand_title_lower = candidate.get("title", "").lower()
    cand_category_lower = candidate.get("category", "").lower()
    
    # Trap check: Java debugging -> don't just recommend Java
    if "java" in curr_text:
        if cand_category_lower == "java" or "java" in cand_title_lower:
            repetition_penalty = 25.0
            
    # AI agents / LLMs trap check: don't recommend identical narrow terms if user seeks broad understanding
    if "phishing" in curr_text or "credentials" in curr_text:
        if "phishing" in cand_title_lower:
            repetition_penalty = 15.0
            
    if "cpu" in curr_text or "gpu" in curr_text:
        if "cpu" in cand_title_lower or "gpu" in cand_title_lower:
            repetition_penalty = 15.0
            
    final_score = interest_match_score + edu_value + career_relevance + engagement - hype_penalty - repetition_penalty
    # Ensure final score is not negative
    final_score = max(0.0, round(final_score, 2))
    
    breakdown = {
        "interest_match": round(interest_match_score, 2),
        "educational_value": round(edu_value, 2),
        "career_relevance": round(career_relevance, 2),
        "engagement_potential": round(engagement, 2),
        "hype_penalty": round(hype_penalty, 2),
        "repetition_penalty": round(repetition_penalty, 2)
    }
    
    return final_score, breakdown, hype_penalty, repetition_penalty

def get_recommendations(profile: dict, current_reel: dict) -> dict:
    """
    Ranks candidates and returns the best recommendation, alternative 'why not' items, and score details.
    """
    candidates = load_candidates()
    if not candidates:
        return {
            "recommended_tech_reel": {
                "title": "Introduction to Software Engineering",
                "category": "Programming",
                "difficulty": "Beginner"
            },
            "why_this_recommendation": "Default recommendation due to database load failure.",
            "why_not": [],
            "score_breakdown": {}
        }
        
    scored_candidates = []
    for cand in candidates:
        score, breakdown, hype_p, rep_p = calculate_score(cand, profile, current_reel)
        scored_candidates.append({
            "candidate": cand,
            "score": score,
            "breakdown": breakdown,
            "hype_penalty": hype_p,
            "repetition_penalty": rep_p
        })
        
    # Sort by score descending
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    best = scored_candidates[0]
    recommended_reel = best["candidate"]
    
    # Select "Why Not" candidates (2-3 items)
    # We want to find:
    # 1. A hype candidate that was rejected
    # 2. A candidate that was too narrow/repetitive (if repetition penalty was applied to it)
    # 3. A candidate that had low interest match
    why_not = []
    
    # Look for a hype candidate
    hype_rejections = [c for c in scored_candidates if c["hype_penalty"] > 10.0]
    if hype_rejections:
        # Sort by hype penalty descending
        hype_rejections.sort(key=lambda x: x["hype_penalty"], reverse=True)
        hr = hype_rejections[0]["candidate"]
        why_not.append({
            "title": hr["title"],
            "status": "Rejected",
            "reason": f"High hype probability ({hr['hype_probability']}%). Exaggerated clickbait claims."
        })
        
    # Look for a repetition penalized candidate
    rep_rejections = [c for c in scored_candidates if c["repetition_penalty"] > 0.0]
    if rep_rejections:
        rep_rejections.sort(key=lambda x: x["repetition_penalty"], reverse=True)
        rr = rep_rejections[0]["candidate"]
        # Determine why it was narrow
        narrow_term = "Java" if "java" in rr["title"].lower() or rr["category"].lower() == "java" else "specific keyword"
        why_not.append({
            "title": rr["title"],
            "status": "Not Selected",
            "reason": f"Too narrow. Although relevant, we avoid repeating the exact same narrow {narrow_term} focus."
        })
        
    # If we don't have enough, pick runners-up or low-match items
    for sc in scored_candidates[1:]:
        if len(why_not) >= 3:
            break
        cand_id = sc["candidate"]["id"]
        # Skip if already added
        if any(w["title"] == sc["candidate"]["title"] for w in why_not):
            continue
        # If it's a runner up
        if sc["score"] > 40:
            why_not.append({
                "title": sc["candidate"]["title"],
                "status": "Not Selected",
                "reason": f"Runner-up. Good option, but scored lower on interest match/relevance than the top pick."
            })
        else:
            why_not.append({
                "title": sc["candidate"]["title"],
                "status": "Not Selected",
                "reason": "Weaker interest match compared to the primary inferred technology domain."
            })
            
    # Format the score breakdown to match exact naming from user requirements
    ui_breakdown = {
        "Interest Match": best["breakdown"]["interest_match"],
        "Educational Value": best["breakdown"]["educational_value"],
        "Career Relevance": best["breakdown"]["career_relevance"],
        "Engagement Potential": best["breakdown"]["engagement_potential"],
        "Hype Penalty": best["breakdown"]["hype_penalty"],
        "Narrowness Penalty": best["breakdown"]["repetition_penalty"],
        "Final Score": best["score"]
    }
    
    return {
        "recommended_tech_reel": recommended_reel,
        "why_not": why_not[:3],  # limit to 3
        "score_breakdown": ui_breakdown
    }
