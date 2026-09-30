#!/usr/bin/env python
"""Generate OpenAPI specification from FastAPI app and save to JSON file."""

import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app


def generate_openapi_spec():
    """Generate and save OpenAPI specification."""

    # Get OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Customize the schema
    openapi_schema["info"]["title"] = "Skills API"
    openapi_schema["info"]["description"] = "Recruiter-facing REST endpoints for skill matching, candidate ranking, and skills gap analysis"
    openapi_schema["info"]["version"] = "1.0"
    openapi_schema["info"]["contact"] = {
        "name": "Development Team",
        "email": "support@teamitserve.com"
    }
    openapi_schema["info"]["license"] = {
        "name": "Proprietary"
    }

    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.teamitserve.com",
            "description": "Production server"
        }
    ]

    # Filter to only include skills endpoints
    if "paths" in openapi_schema:
        paths_to_keep = {}
        for path, methods in openapi_schema["paths"].items():
            if "/api/v1/skills" in path:
                paths_to_keep[path] = methods
        openapi_schema["paths"] = paths_to_keep

    # Save to file
    output_file = "docs/openapi_skills_api.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✅ OpenAPI specification generated: {output_file}")
    print(f"\nSpecification Summary:")
    print(f"- Title: {openapi_schema['info']['title']}")
    print(f"- Version: {openapi_schema['info']['version']}")
    print(f"- Endpoints: {len(openapi_schema.get('paths', {}))}")
    print(f"- Servers: {len(openapi_schema.get('servers', []))}")

    return output_file


if __name__ == "__main__":
    try:
        generate_openapi_spec()
    except Exception as e:
        print(f"❌ Error generating OpenAPI spec: {e}")
        sys.exit(1)
