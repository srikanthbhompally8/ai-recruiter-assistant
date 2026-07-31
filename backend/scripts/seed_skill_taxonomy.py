"""Script to seed initial skill taxonomy data"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from app.config import settings
from app.models import Base
from app.database import SessionLocal

# Skill taxonomy data
SKILLS = {
    "Programming Languages": {
        "Python": {"description": "Python programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Java": {"description": "Java programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "JavaScript": {"description": "JavaScript programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "TypeScript": {"description": "TypeScript programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Go": {"description": "Go programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Rust": {"description": "Rust programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "C++": {"description": "C++ programming language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "SQL": {"description": "SQL database language", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "Cloud Platforms": {
        "AWS": {"description": "Amazon Web Services", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Azure": {"description": "Microsoft Azure", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Google Cloud": {"description": "Google Cloud Platform", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Kubernetes": {"description": "Kubernetes container orchestration", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "Databases": {
        "PostgreSQL": {"description": "PostgreSQL relational database", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "MongoDB": {"description": "MongoDB NoSQL database", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Redis": {"description": "Redis in-memory cache", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Elasticsearch": {"description": "Elasticsearch search engine", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "DynamoDB": {"description": "Amazon DynamoDB", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "DevOps & Tools": {
        "Docker": {"description": "Docker containerization", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "CI/CD": {"description": "Continuous Integration/Deployment", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Git": {"description": "Git version control", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Jenkins": {"description": "Jenkins automation server", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Terraform": {"description": "Terraform infrastructure as code", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "AI/ML": {
        "Machine Learning": {"description": "Machine Learning fundamentals", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Deep Learning": {"description": "Deep Learning frameworks", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "TensorFlow": {"description": "TensorFlow framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "PyTorch": {"description": "PyTorch framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "NLP": {"description": "Natural Language Processing", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "Frontend": {
        "React": {"description": "React JavaScript library", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Vue.js": {"description": "Vue.js framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Angular": {"description": "Angular framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "HTML/CSS": {"description": "HTML and CSS markup", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Tailwind CSS": {"description": "Tailwind CSS utility framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "Backend Frameworks": {
        "FastAPI": {"description": "FastAPI Python framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Django": {"description": "Django Python framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Flask": {"description": "Flask Python framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Spring Boot": {"description": "Spring Boot Java framework", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Node.js": {"description": "Node.js JavaScript runtime", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
    "Data Engineering": {
        "Apache Spark": {"description": "Apache Spark data processing", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Data Pipeline": {"description": "Data pipeline development", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "ETL": {"description": "Extract Transform Load processes", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        "Apache Airflow": {"description": "Apache Airflow workflow orchestration", "proficiency_levels": ["Beginner", "Intermediate", "Advanced", "Expert"]},
    },
}


def seed_skills():
    """Seed the skill taxonomy database"""
    db = SessionLocal()

    try:
        # Import models here to avoid circular imports
        from app.models.skill import SkillTaxonomy

        for category, skills in SKILLS.items():
            for skill_name, skill_data in skills.items():
                # Check if skill already exists
                existing = db.query(SkillTaxonomy).filter_by(skill_name=skill_name).first()
                if existing:
                    print(f"⏭️  Skipping {skill_name} (already exists)")
                    continue

                skill = SkillTaxonomy(
                    id=uuid.uuid4(),
                    skill_name=skill_name,
                    category=category,
                    description=skill_data.get("description"),
                    proficiency_levels=skill_data.get("proficiency_levels"),
                    is_active=True,
                )
                db.add(skill)
                print(f"✅ Added {skill_name} ({category})")

        db.commit()
        print(f"\n✅ Skill taxonomy seeding complete!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding skills: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_skills()
