import re

KEYWORDS = {
    "Software Engineering": [
        "programming", "developer", "debugging", "software", "java", "python",
        "c\\+\\+", "coding", "backend", "code", "frontend", "dev", "monolith"
    ],
    "Artificial Intelligence": [
        "ai", "artificial intelligence", "llm", "machine learning", "deep learning",
        "ai agents", "generative ai", "neural network", "chatgpt", "transformers",
        "rag", "vector database"
    ],
    "Cybersecurity": [
        "cybersecurity", "phishing", "malware", "network security", "password",
        "credentials", "hacking", "security", "attack", "injection", "authentication",
        "mfa"
    ],
    "Hardware": [
        "cpu", "gpu", "processor", "laptop", "ram", "ssd", "graphics card",
        "hardware", "chip", "m4", "hardware"
    ],
    "Cloud": [
        "aws", "azure", "gcp", "cloud", "deployment", "server", "devops",
        "docker", "kubernetes", "serverless", "microservices"
    ],
    "DSA": [
        "array", "linked list", "tree", "graph", "algorithm", "data structures",
        "coding interview", "leetcode", "search", "sort"
    ]
}

DISPLAY_NAMES = {
    "Software Engineering": "Software Engineering / Programming",
    "Artificial Intelligence": "Artificial Intelligence",
    "Cybersecurity": "Cybersecurity",
    "Hardware": "Hardware / Computer Technology",
    "Cloud": "Cloud",
    "DSA": "DSA / Software Engineering"
}

RELATED_INTERESTS = {
    "Software Engineering": ["Programming", "Clean Code", "Backend Development"],
    "Artificial Intelligence": ["Machine Learning", "LLMs", "AI Agents"],
    "Cybersecurity": ["Network Security", "Application Security", "Penetration Testing"],
    "Hardware": ["Processor Architecture", "System Performance", "Hardware Engineering"],
    "Cloud": ["DevOps", "Infrastructure as Code", "Scalability"],
    "DSA": ["Algorithms", "Coding Interviews", "Data Structures"]
}

def analyze_locally(description: str, caption: str) -> dict:
    """
    Deterministic rule-based inference of broad interests from description and caption.
    """
    text = (description + " " + caption).lower()
    
    matches = {}
    found_keywords = {}
    
    for category, keywords in KEYWORDS.items():
        count = 0
        found = []
        for kw in keywords:
            pattern = rf"\b{kw}\b"
            if kw == "c\\+\\+":
                pattern = r"c\+\+"
            found_instances = re.findall(pattern, text)
            if found_instances:
                count += len(found_instances)
                found.append(kw.replace("\\", ""))
        matches[category] = count
        found_keywords[category] = found
        
    # Get category with highest count
    best_cat = max(matches, key=matches.get)
    best_count = matches[best_cat]
    
    # Fallback to Software Engineering if no keywords matched
    if best_count == 0:
        best_cat = "Software Engineering"
        
    primary_interest = DISPLAY_NAMES[best_cat]
    related = RELATED_INTERESTS[best_cat]
    
    # Confidence and Strength
    if best_count >= 3:
        confidence = "High"
        strength = min(75 + best_count * 3, 98)
    elif best_count >= 1:
        confidence = "Medium"
        strength = min(50 + best_count * 10, 74)
    else:
        confidence = "Low"
        strength = 35
        
    # Generate evidence
    if best_count > 0:
        evidence = [f"Detected technology keyword '{kw}' in Reel text." for kw in found_keywords[best_cat][:4]]
        evidence.append(f"Contextual indicators strongly point towards {best_cat}.")
    else:
        evidence = [
            "No specific niche keywords detected in Reel text.",
            "Defaulting to base interest profile: Programming / Software Development."
        ]
        
    return {
        "primary_interest": primary_interest,
        "confidence": confidence,
        "interest_strength": strength,
        "evidence": evidence,
        "related_interests": related
    }
