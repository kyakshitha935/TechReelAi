import unittest
import os
import sys

# Add root folder to python path to ensure backend imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.fallback_engine import analyze_locally
from backend.recommender import calculate_score, get_recommendations
from backend.main import app, generate_local_explanation
from fastapi.testclient import TestClient

class TestTechScrollPipeline(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)
        
        # Sample current reel inputs for testing
        self.java_input = {
            "description": "A software developer is debugging a Java application late at night. After several hours, they finally discover the bug.",
            "caption": "When your Java code finally works after 3 hours 😂"
        }
        self.ai_input = {
            "description": "An AI engineer explains how large language models and AI agents use tools to complete tasks.",
            "caption": "Understanding how AI agents actually work."
        }
        self.cyber_input = {
            "description": "A cybersecurity expert demonstrates how phishing attacks trick users into entering their passwords.",
            "caption": "Never enter credentials without checking the URL."
        }
        self.hardware_input = {
            "description": "A technology reviewer compares CPU cores, GPU performance and laptop processors.",
            "caption": "More cores don't always mean better performance."
        }
        self.cloud_input = {
            "description": "A devops specialist explains AWS EC2 deployment, Docker containers, and load balancers.",
            "caption": "Setting up production backend infrastructure."
        }
        self.dsa_input = {
            "description": "A teacher explaining how a binary search algorithm solves a tree-based problem.",
            "caption": "Cracking the technical coding interview."
        }
    def test_local_fallback_java(self):
        """Test that Java inputs resolve to Software Engineering / Programming interest."""
        profile = analyze_locally(self.java_input["description"], self.java_input["caption"])
        self.assertEqual(profile["primary_interest"], "Software Engineering / Programming")
        self.assertTrue(any("java" in ev.lower() for ev in profile["evidence"]))

    def test_local_fallback_ai(self):
        """Test that AI inputs resolve to Artificial Intelligence."""
        profile = analyze_locally(self.ai_input["description"], self.ai_input["caption"])
        self.assertEqual(profile["primary_interest"], "Artificial Intelligence")
        self.assertTrue(any("ai" in ev.lower() or "llm" in ev.lower() for ev in profile["evidence"]))

    def test_local_fallback_cyber(self):
        """Test that cybersecurity inputs resolve to Cybersecurity."""
        profile = analyze_locally(self.cyber_input["description"], self.cyber_input["caption"])
        self.assertEqual(profile["primary_interest"], "Cybersecurity")
        self.assertTrue(any("phishing" in ev.lower() or "credentials" in ev.lower() for ev in profile["evidence"]))

    def test_local_fallback_hardware(self):
        """Test that processor/graphics inputs resolve to Hardware."""
        profile = analyze_locally(self.hardware_input["description"], self.hardware_input["caption"])
        self.assertEqual(profile["primary_interest"], "Hardware / Computer Technology")

    def test_local_fallback_cloud(self):
        """Test that server/deployment inputs resolve to Cloud."""
        profile = analyze_locally(self.cloud_input["description"], self.cloud_input["caption"])
        self.assertEqual(profile["primary_interest"], "Cloud")

    def test_local_fallback_dsa(self):
        """Test that data structures inputs resolve to DSA / Software Engineering."""
        profile = analyze_locally(self.dsa_input["description"], self.dsa_input["caption"])
        self.assertEqual(profile["primary_interest"], "DSA / Software Engineering")

    def test_hype_filtering(self):
        """Verify that hype candidates are penalized heavily."""
        profile = {
            "primary_interest": "Artificial Intelligence",
            "related_interests": ["Machine Learning", "LLMs"]
        }
        # H003 is "Learn All of AI in One Weekend" (Hype)
        hype_cand = {
            "id": "H003",
            "title": "Learn All of AI in One Weekend",
            "description": "Learn generative AI, deep learning, LLMs in a single weekend.",
            "category": "AI",
            "educational_value": 20,
            "career_relevance": 12,
            "engagement_potential": 92,
            "hype_probability": 95
        }
        score, breakdown, hype_penalty, rep_penalty = calculate_score(hype_cand, profile, self.ai_input)
        self.assertGreater(hype_penalty, 20.0)
        self.assertGreater(breakdown["hype_penalty"], 20.0)

    def test_repetition_penalty_java_trap(self):
        """Verify that narrow Java candidates get penalized for Java inputs to prioritize broader DSA/Career."""
        profile = {
            "primary_interest": "Software Engineering / Programming",
            "related_interests": ["Programming", "Clean Code"]
        }
        # T011 is "Java Memory Management" (Narrow Java)
        java_cand = {
            "id": "T011",
            "title": "Java Memory Management: Heap vs Stack",
            "category": "Java",
            "educational_value": 92,
            "career_relevance": 85,
            "engagement_potential": 76,
            "hype_probability": 3
        }
        # T001 is "How Software Engineers Prepare for Coding Interviews" (Broad DSA/Career)
        dsa_cand = {
            "id": "T001",
            "title": "How Software Engineers Prepare for Coding Interviews",
            "category": "DSA",
            "educational_value": 92,
            "career_relevance": 95,
            "engagement_potential": 80,
            "hype_probability": 5
        }
        
        java_score, _, _, java_rep = calculate_score(java_cand, profile, self.java_input)
        dsa_score, _, _, dsa_rep = calculate_score(dsa_cand, profile, self.java_input)
        
        self.assertEqual(java_rep, 25.0)
        self.assertEqual(dsa_rep, 0.0)
        self.assertGreater(dsa_score, java_score, "DSA/Career candidate should outscore the narrow Java candidate due to repetition penalty.")

    def test_empty_input_error(self):
        """Verify that sending empty values yields a 400 Bad Request error."""
        response = self.client.post("/api/recommend", json={"description": "", "caption": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Please enter a Reel description or caption.", response.json()["detail"])

    def test_api_recommend_dynamic(self):
        """Verify that the recommendations change dynamically between AI, Cybersecurity, and Hardware inputs."""
        # 1. Post AI input
        res_ai = self.client.post("/api/recommend", json=self.ai_input)
        self.assertEqual(res_ai.status_code, 200)
        data_ai = res_ai.json()
        self.assertEqual(data_ai["interest_detected"]["topic"], "Artificial Intelligence")
        self.assertIn(data_ai["category"], ["AI", "Technology News"])
        self.assertIn("interest_path", data_ai)
        self.assertIsInstance(data_ai["interest_path"], list)
        
        # 2. Post Cybersecurity input
        res_sec = self.client.post("/api/recommend", json=self.cyber_input)
        self.assertEqual(res_sec.status_code, 200)
        data_sec = res_sec.json()
        self.assertEqual(data_sec["interest_detected"]["topic"], "Cybersecurity")
        self.assertEqual(data_sec["category"], "Cybersecurity")
        
        # 3. Post Hardware input
        res_hw = self.client.post("/api/recommend", json=self.hardware_input)
        self.assertEqual(res_hw.status_code, 200)
        data_hw = res_hw.json()
        self.assertEqual(data_hw["interest_detected"]["topic"], "Hardware / Computer Technology")
        
        # Confirm they returned different recommended reels
        self.assertNotEqual(
            data_ai["recommended_tech_reel"]["title"],
            data_sec["recommended_tech_reel"]["title"],
            "Recommendations should change dynamically based on input"
        )
        self.assertNotEqual(
            data_sec["recommended_tech_reel"]["title"],
            data_hw["recommended_tech_reel"]["title"],
            "Recommendations should change dynamically based on input"
        )

    def test_health_endpoint(self):
        """Verify that the health check endpoint returns 200 OK."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

if __name__ == "__main__":
    unittest.main()
