"""Matching Engine Service using Bedrock Embeddings"""
import json
import logging
from typing import List, Dict, Any
import boto3
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)


class MatchingEngineService:
    """Service for candidate-to-job matching using embeddings"""

    def __init__(self):
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
        )
        self.embeddings_model = settings.BEDROCK_EMBEDDINGS_MODEL

    def calculate_match(
        self,
        candidate_skills: List[str],
        job_required_skills: List[str],
        job_nice_to_have_skills: List[str] = None,
        candidate_experience: int = 0,
        job_experience_required: int = 0,
    ) -> Dict[str, Any]:
        """
        Calculate match score between candidate and job

        Args:
            candidate_skills: List of candidate skills
            job_required_skills: List of required skills
            job_nice_to_have_skills: List of nice-to-have skills
            candidate_experience: Candidate's years of experience
            job_experience_required: Required years of experience

        Returns:
            Dictionary with match details and scores
        """
        try:
            job_nice_to_have_skills = job_nice_to_have_skills or []

            # Calculate skill matches
            matched_required = [
                s for s in candidate_skills if s.lower() in [x.lower() for x in job_required_skills]
            ]
            matched_nice = [
                s for s in candidate_skills if s.lower() in [x.lower() for x in job_nice_to_have_skills]
            ]
            missing_skills = [
                s for s in job_required_skills if s.lower() not in [x.lower() for x in candidate_skills]
            ]

            # Calculate skills match score
            skills_match = 0.0
            if job_required_skills:
                skills_match = (len(matched_required) / len(job_required_skills)) * 100

            # Calculate experience match score
            experience_match = 100.0
            if job_experience_required > 0:
                if candidate_experience >= job_experience_required:
                    experience_match = 100.0
                else:
                    experience_match = (candidate_experience / job_experience_required) * 100

            # Calculate overall score (weighted average)
            # 70% skills, 30% experience
            overall_score = (skills_match * 0.7) + (experience_match * 0.3)

            # Determine recommendation
            if overall_score >= 80:
                recommendation = "recommended"
            elif overall_score >= 60:
                recommendation = "marginal"
            else:
                recommendation = "not_recommended"

            return {
                "skills_match": round(skills_match, 2),
                "experience_match": round(experience_match, 2),
                "overall_score": round(overall_score, 2),
                "matched_skills": matched_required + matched_nice,
                "missing_skills": missing_skills,
                "recommendation": recommendation,
                "details": {
                    "required_matched": len(matched_required),
                    "required_total": len(job_required_skills),
                    "nice_to_have_matched": len(matched_nice),
                    "nice_to_have_total": len(job_nice_to_have_skills),
                    "candidate_experience": candidate_experience,
                    "job_experience_required": job_experience_required,
                },
            }

        except Exception as e:
            logger.error(f"Matching engine error: {e}")
            raise

    def get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for text using Bedrock Titan Embeddings

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.embeddings_model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(
                    {
                        "inputText": text,
                    }
                ),
            )

            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding")
            return embedding

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using cosine similarity

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        try:
            emb1 = self.get_embeddings(text1)
            emb2 = self.get_embeddings(text2)

            # Cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            raise


# Create singleton instance
matching_engine = MatchingEngineService()
