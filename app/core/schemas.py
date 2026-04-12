from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


# =========================
# PROJECT TYPES
# =========================

class ProjectType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    TELEGRAM_BOT = "telegram_bot"
    MOBILE_EXPO = "mobile_expo"
    MOBILE_FLUTTER = "mobile_flutter"


# =========================
# AGENTS
# =========================

class AgentName(str, Enum):
    PLANNER = "planner"
    SPEC = "spec"
    ARCHITECT = "architect"
    FRONTEND = "frontend"
    BACKEND = "backend"
    MOBILE = "mobile"
    QA = "qa"
    FIX = "fix"
    VALIDATOR = "validator"
    DEPLOY = "deploy"


# =========================
# ROUTING TASK
# =========================

class AgentTask(BaseModel):
    agent: AgentName
    goal: str
    input_refs: List[str] = []
    output_ref: str


class RoutePlan(BaseModel):
    project_type: ProjectType
    needs_frontend: bool
    needs_backend: bool
    needs_mobile: bool
    tasks: List[AgentTask]


# =========================
# ARTIFACT (самое важное)
# =========================

class Artifact(BaseModel):
    ref: str
    kind: str
    data: Dict[str, Any]


# =========================
# BUILD RESULT
# =========================

class BuildResult(BaseModel):
    ok: bool
    project_type: ProjectType
    logs: List[str] = []
    errors: List[str] = []
    run_command: Optional[str] = None


# =========================
# VALIDATION RESULT
# =========================

class ValidationResult(BaseModel):
    ok: bool
    checks_passed: List[str] = []
    checks_failed: List[str] = []
    errors: List[str] = []


# =========================
# DEPLOY RESULT
# =========================

class DeployResult(BaseModel):
    ok: bool
    url: Optional[str] = None
    logs: List[str] = []
    errors: List[str] = []