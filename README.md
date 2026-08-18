# TechScroll AI — Final Hackathon Build

TechScroll AI is an AI-powered recommendation agent that analyzes the short-form video Reels a student interacts with, infers their underlying technology-related interests, and recommends engaging, high-quality educational technology Reels that match those interests.

The system is designed to combat low-quality "hype" or clickbait content (e.g., "Become an engineer in 7 days") and direct students towards educational value and career relevance. It also solves the **repetition trap** (e.g., if you watch a Java debugging meme, it doesn't just recommend more Java memes; it infers a broader "Software Engineering" interest and recommends structured content like DSA or coding interview prep).

## Key Features

1. **Context-Aware Interest Inference**: Understands the semantic meaning of descriptions and captions beyond simple keyword matching.
2. **Quality-Aware Ranking**: Penalizes or rejects exaggerated clickbait/hype reels.
3. **Explainable Recommendations**: Displays the logical path from the inferred interest to the recommended tech Reel.
4. **Adaptive Backend Pipeline**:
   - **Gemini (when available)**: Performs deep semantic reasoning and explains the recommendation.
   - **Deterministic Fallback (when offline)**: Heuristic keyword mapping ensures a reliable, dynamic, and non-crashed demo.
5. **Interactive Hackathon Dashboard**:
   - Collapsible score breakdown showing exactly how the recommendation was ranked.
   - "Why Not These" comparison panel displaying alternative candidates and reasons they were not selected.
   - Beautiful, responsive glassmorphism dark theme.

## Project Structure

```
techscroll_ai/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── ai_service.py
│   ├── recommender.py
│   └── fallback_engine.py
│
├── data/
│   └── candidate_reels.json
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── tests/
│   └── test_pipeline.py
│
├── .env.example
├── requirements.txt
└── README.md
```

## Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key (Optional)**:
   Create a `.env` file from `.env.example` and add your `GEMINI_API_KEY`:
   ```bash
   copy .env.example .env
   ```
   *Note: If no API key is specified, the application automatically falls back to local fallback mode with "Demo Mode" header, while remaining fully dynamic.*

3. **Run Automated Tests**:
   ```bash
   python -m unittest tests/test_pipeline.py
   ```

4. **Start the Dev Server**:
   ```bash
   python -m uvicorn backend.main:app --port 8000
   ```

5. **Access the Web Dashboard**:
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.
