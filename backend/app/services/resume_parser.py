"""Resume Parsing Service using AWS Bedrock Claude"""
import json
import logging
from typing import Dict, Any
import boto3
from app.config import settings

logger = logging.getLogger(__name__)


class ResumeParserService:
    """Service for parsing resumes using Claude on Bedrock"""

    def __init__(self):
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
        )
        self.model_id = settings.BEDROCK_MODEL_ID

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text and extract structured information

        Args:
            resume_text: Raw resume text content

        Returns:
            Dictionary with parsed resume data
        """
        try:
            prompt = self._build_parsing_prompt(resume_text)

            message = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-06-01",
                        "max_tokens": 2000,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                    }
                ),
            )

            response_body = json.loads(message["body"].read())
            response_text = response_body["content"][0]["text"]

            # Parse JSON from response
            parsed_data = self._extract_json(response_text)
            logger.info("Resume parsed successfully")
            return parsed_data

        except Exception as e:
            logger.error(f"Resume parsing error: {e}")
            raise

    def _build_parsing_prompt(self, resume_text: str) -> str:
        """Build the prompt for Claude to parse resume"""
        return f"""You are an expert resume parser. Extract the following information from the resume and return it as valid JSON.

Resume Text:
{resume_text}

Extract and return the following information as JSON (use null for missing fields):
{{
    "full_name": "Full name of the candidate",
    "email": "Email address",
    "phone": "Phone number",
    "current_title": "Current job title",
    "current_company": "Current company name",
    "experience_years": "Total years of experience (number)",
    "skills": ["List", "of", "technical", "skills"],
    "education": [
        {{
            "degree": "Bachelor/Master/etc",
            "field": "Field of study",
            "school": "University name",
            "year": 2020
        }}
    ],
    "experience": [
        {{
            "title": "Job title",
            "company": "Company name",
            "start_year": 2020,
            "end_year": 2023,
            "description": "Job description"
        }}
    ],
    "certifications": ["Certification 1", "Certification 2"],
    "languages": ["English", "Spanish"],
    "summary": "Professional summary"
}}

Return ONLY the JSON object, no additional text."""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Claude response"""
        try:
            # Try direct parse first
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            raise ValueError("Could not extract JSON from response")


# Create singleton instance
resume_parser = ResumeParserService()
