from typing import Dict, List, Any
from dataclasses import dataclass, field
from app.core.schemas import Artifact


@dataclass
class ProjectState:
    # =========================
    # BASIC
    # =========================
    task: str
    workspace: str
    project_type: str | None = None

    # =========================
    # CORE MEMORY
    # =========================
    artifacts: Dict[str, Artifact] = field(default_factory=dict)

    # =========================
    # META
    # =========================
    decisions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    # =========================
    # EXECUTION TRACKING
    # =========================
    run_history: List[Dict[str, Any]] = field(default_factory=list)

    build_attempts: int = 0
    validation_attempts: int = 0
    deploy_attempts: int = 0

    # =========================
    # ARTIFACT METHODS
    # =========================
    def add_artifact(self, artifact: Artifact):
        self.artifacts[artifact.ref] = artifact

    def get_artifact(self, ref: str) -> Artifact:
        if ref not in self.artifacts:
            raise ValueError(f"Artifact '{ref}' not found")
        return self.artifacts[ref]

    def has_artifact(self, ref: str) -> bool:
        return ref in self.artifacts

    # =========================
    # LOGGING
    # =========================
    def log_step(self, agent: str, result_ref: str):
        self.run_history.append({
            "agent": agent,
            "result": result_ref
        })

    # =========================
    # SNAPSHOT (для debug)
    # =========================
    def snapshot(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "workspace": self.workspace,
            "project_type": self.project_type,
            "artifacts": list(self.artifacts.keys()),
            "decisions": self.decisions,
            "assumptions": self.assumptions,
            "open_questions": self.open_questions,
            "build_attempts": self.build_attempts,
            "validation_attempts": self.validation_attempts,
            "deploy_attempts": self.deploy_attempts,
            "history": self.run_history,
        }