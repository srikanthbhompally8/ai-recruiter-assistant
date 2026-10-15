"""AWS Bedrock Service - Job Description Parsing"""

import json
import logging
import boto3
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class BedrockService:
    """Service for AWS Bedrock AI operations using Converse API"""

    def __init__(self):
        """Initialize Bedrock client"""
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            self.model_id = settings.BEDROCK_MODEL_ID
            logger.info(f"Bedrock client initialized with model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.client = None

    def parse_job_description(self, job_description: str) -> Optional[Dict[str, Any]]:
        """
        Parse job description using Bedrock AI (Converse API)

        Args:
            job_description: Raw job description text

        Returns:
            Parsed job data with extracted fields or None if failed
        """
        if not self.client:
            logger.error("Bedrock client not initialized")
            return None

        try:
            prompt = f"""Parse the following job description and extract structured data.
Return ONLY valid JSON with these fields:
- job_title (string)
- company (string)
- required_skills (array of strings)
- nice_to_have_skills (array of strings)
- years_required (integer)
- job_type (string: full-time, part-time, contract)
- salary_range (object with min and max)
- job_level (string: junior, mid, senior)
- responsibilities (array of strings, top 3-5)

Job Description:
{job_description}

Return ONLY the JSON object, no other text."""

            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                inferenceConfig={
                    "maxTokens": 1024,
                    "temperature": 0.7
                }
            )

            logger.info(f"Bedrock response received for job parsing")

            # Extract content from Converse API response
            if 'output' in response and 'message' in response['output']:
                message = response['output']['message']
                if 'content' in message and len(message['content']) > 0:
                    content = message['content'][0].get('text', '')

                    # Clean up response (remove markdown code blocks if present)
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()

                    # Parse JSON
                    parsed_data = json.loads(content)
                    logger.info(f"Job description parsed: {parsed_data.get('job_title', 'Unknown')}")

                    return {
                        "status": "success",
                        "data": parsed_data
                    }

            logger.error("No content in Bedrock response")
            return {"status": "error", "message": "No content in response"}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bedrock response JSON: {e}")
            return {"status": "error", "message": f"JSON parse error: {str(e)}"}
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            return {"status": "error", "message": f"Bedrock error: {str(e)}"}

    def extract_skills(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract skills from text using Bedrock

        Args:
            text: Text to extract skills from

        Returns:
            Dictionary with extracted skills or None
        """
        if not self.client:
            logger.error("Bedrock client not initialized")
            return None

        try:
            prompt = f"""Extract all technical and soft skills mentioned in this text.
Return ONLY valid JSON with these fields:
- technical_skills (array of strings)
- soft_skills (array of strings)
- proficiency_levels (object with skill names as keys and levels as values: beginner/intermediate/advanced/expert)

Text:
{text}

Return ONLY the JSON object."""

            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                inferenceConfig={
                    "maxTokens": 512,
                    "temperature": 0.7
                }
            )

            # Extract content from response
            if 'output' in response and 'message' in response['output']:
                message = response['output']['message']
                if 'content' in message and len(message['content']) > 0:
                    content = message['content'][0].get('text', '')
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()

                    parsed_data = json.loads(content)
                    logger.info(f"Skills extracted: {len(parsed_data.get('technical_skills', []))} technical")

                    return {
                        "status": "success",
                        "data": parsed_data
                    }

            logger.error("No content in skill extraction response")
            return {"status": "error", "message": "No content in response"}

        except Exception as e:
            logger.error(f"Skill extraction error: {e}")
            return {"status": "error", "message": str(e)}


# Create singleton instance
bedrock_service = BedrockService()
