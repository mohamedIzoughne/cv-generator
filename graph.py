from enum import Enum
from typing import List
from pydantic import BaseModel, Field, model_validator
from typing import TypedDict, List, Dict

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


class LoadedDocument(TypedDict):
    title: str
    path: str
    content: str

class XYZPlan(BaseModel):
    accomplishment: str = Field(description="[X] Core engineering action or built feature delivered.")
    measurement: str = Field(description="[Y] Grounded metric from KB (e.g., '4.87 MAE') OR strict operational scope/constraints if no numeric metric exists (e.g., 'real-time asynchronous throughput').")
    mechanism: str = Field(description="[Z] Architectural mechanism, protocol, design pattern, or tech stack used.")

class SelectedEntryBlueprint(BaseModel):
    entry_id: str = Field(description="Exact identifier or title matching the entry in the Obsidian KB.")
    bullet_allocation: int = Field(ge=1, le=4, description="Number of bullets allocated (3-4 for primary, 1-2 for secondary).")
    xyz_plans: List[XYZPlan] = Field(description="Structured breakdown of each bullet's narrative blueprint matching the XYZ formula.")

class SelectionBlueprint(BaseModel):
    section_order: List[str] = Field(description="Ordered list of sections e.g., ['Education', 'Experience', 'Projects', 'Technical Skills']")
    skill_rows: Dict[str, List[str]] = Field(description="Categorized technical skill rows ordered to mirror JD priority buckets")
    selected_entries: List[SelectedEntryBlueprint] = Field(description="The curated 'Best 4-5' entries with their allocated bullet blueprints.")

class CVGenerationResult(BaseModel):
    latex_source_code: str = Field(description="The complete, raw, compilable LaTeX source code string adhering strictly to single-column article rules.")


class graph(TypedDict):
    raw_jd: str # (input job description)
    jd_analysis: JDAnalysis # (from your Pydantic schema)
    knowledge_base_path: str
    exemplars_path: str
    full_knowledge: str
    matched_examples: str
    matched_examples_latex: str
    selection_blueprint: dict # (or a Pydantic model for Node 3A)
    latex_code: str # (raw output from Node 3B)
    # audit_result: dict # (from Node 4)
    retry_count: int # (tracks Node 4 loops, starting at 0)
    # compression_retries: int # (tracks Node 5 PDF overflow loops, starting at 0)
    # pdf_path: str
    # documents: List[LoadedDocument]
