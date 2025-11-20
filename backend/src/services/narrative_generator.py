import json
import logging

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.db.database import GEMINI_API_KEY

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_SUMMARY_LENGTH = 200 # Define a constant for the maximum summary length

class NarrativeGenerator:
    def __init__(self):
        self.model = self._get_gemini_model()

    def _get_gemini_model(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=GEMINI_API_KEY)
        # For text-only input, use the gemini-pro model
        return genai.GenerativeModel('gemini-pro')

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def generate_narrative(self, repo_details: dict) -> str:
        """
        Generates a comprehensive narrative based on repository details using an LLM.
        """
        file_structure = repo_details.get('file_structure', [])
        commit_history = repo_details.get('commit_history', [])

        prompt = f"""
        Generate a comprehensive narrative for a software project based on the following information:

        Repository Details:
        - Name: {repo_details.get('name', 'N/A')}
        - Description: {repo_details.get('description', 'N/A')}
        - Main Language: {repo_details.get('main_language', 'N/A')}
        - Languages: {json.dumps(repo_details.get('languages', {}))}
        - Tech Stack: {', '.join(repo_details.get('tech_stack', ['None']))}
        - Topics: {', '.join(repo_details.get('topics', ['None']))}
        - License: {repo_details.get('license', 'N/A')}
        - Stars: {repo_details.get('stargazers_count', 0)}
        - Forks: {repo_details.get('forks_count', 0)}
        - Open Issues: {repo_details.get('open_issues_count', 0)}
        - Open Pull Requests: {repo_details.get('open_pull_requests_count', 0)}
        - Contributors: {', '.join(repo_details.get('contributors', ['None']))}
        - Total Files: {repo_details.get('file_count', 0)}
        - Total Commits: {repo_details.get('commit_count', 0)}

        File Structure (first 10 files):
        {chr(10).join([f"- {f['path']}" for f in file_structure[:10]])}

        Commit History (last 5 commits):
        {chr(10).join([f"- {c['message']} by {c['author_name']} on {c['date']}" for c in commit_history[:5]])}

        Based on this data, provide a narrative that covers:
        1.  **Project Overview**: What is the project about? What problem does it solve?
        2.  **Technical Aspects**: Highlight key technologies, architectural patterns (inferred from file structure), and notable features.
        3.  **Development Activity**: Summarize the recent development efforts and project maturity.
        4.  **Potential Impact/Value**: What is the significance or potential of this project?

        Ensure the narrative is engaging, informative, and suitable for a technical audience.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error generating narrative: {e}")
            return "Error generating narrative."

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def generate_recruiter_summary(self, repo_analysis: dict) -> str:
        """
        Generates a concise, non-technical summary focused on business value for a recruiter using an LLM.
        """
        prompt = f"""
        Generate a concise, non-technical summary (2-3 sentences, max {MAX_SUMMARY_LENGTH} characters) for a recruiter about the following software project. Focus on business value, key features, and the impact of the technologies used, avoiding deep technical jargon.

        Project Name: {repo_analysis.get('name', 'N/A')}
        Description: {repo_analysis.get('description', 'N/A')}
        Main Language: {repo_analysis.get('main_language', 'N/A')}
        Languages: {json.dumps(repo_analysis.get('languages', {}))}
        Tech Stack: {', '.join(repo_analysis.get('tech_stack', ['None']))}
        Topics: {', '.join(repo_analysis.get('topics', ['None']))}
        Stars: {repo_analysis.get('stargazers_count', 0)}
        Forks: {repo_analysis.get('forks_count', 0)}
        Open Issues Count: {repo_analysis.get('open_issues_count', 0)}
        Open Pull Requests Count: {repo_analysis.get('open_pull_requests_count', 0)}
        Contributors: {', '.join(repo_analysis.get('contributors', ['None']))}
        Total Files: {repo_analysis.get('file_count', 0)}
        Total Commits: {repo_analysis.get('commit_count', 0)}

        Highlight how this project demonstrates valuable skills and delivers practical solutions.
        """
        try:
            response = await self.model.generate_content_async(prompt)
            summary = response.text
            if len(summary) > MAX_SUMMARY_LENGTH:
                summary = summary[:MAX_SUMMARY_LENGTH - 3] + "..."
            return summary
        except Exception as e:
            logging.error(f"Error generating recruiter summary: {e}")
            return "Error generating recruiter summary."
