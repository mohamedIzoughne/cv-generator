from enum import Enum
from typing import List
from pydantic import BaseModel, Field, model_validator

class TargetRole(str, Enum):
    AI_ML_ENGINEER = "AI_ML_Engineer"                 # Covers Applied AI, LLMs, RAG, and MLOps/Infra
    SOFTWARE_BACKEND_ENGINEER = "Software_Backend_Engineer" # Covers Backend, Systems, and Full-Stack
    DATA_ENGINEER = "Data_Engineer"                   # Covers ETL, Kafka, Spark, Warehousing
    UNRELATED = "Unrelated"

class SeniorityLevel(str, Enum):
    INTERNSHIP = "internship"
    JUNIOR = "junior"
    MID = "mid"

class JDAnalysis(BaseModel):
    reasoning: str = Field(
        description="Step-by-step analysis of the core engineering focus and why it maps to the chosen target role."
    )
    is_related: bool = Field(
        description="True ONLY if target_role is AI_ML_Engineer, Software_Backend_Engineer, or Data_Engineer."
    )
    target_role: TargetRole = Field(
        description=(
            "The primary consolidated target role. Must be 'Unrelated' if the job is frontend-only, "
            "mobile-only, manual QA, IT support, sales, or outside software/data/AI engineering."
        )
    )
    sub_focus: List[str] = Field(
        description="Specific technical sub-areas required (e.g., ['API Design', 'Model Integration', 'MLOps', 'Distributed Systems']). Used to guide CV project tailoring."
    )
    must_have_skills: List[str] = Field(
        description="Extracted hard technologies and tools (e.g., Python, FastAPI, Docker, PyTorch, PostgreSQL)."
    )
    domain_keywords: List[str] = Field(
        description="Architectural concepts (e.g., microservices, RAG, inference optimization, ETL, CI/CD)."
    )
    seniority_level: SeniorityLevel

    @model_validator(mode="after")
    def enforce_role_consistency(self) -> "JDAnalysis":
        self.is_related = self.target_role != TargetRole.UNRELATED
        if not self.is_related:
            self.sub_focus = []
        return self