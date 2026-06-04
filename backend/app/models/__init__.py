"""Import all models so Alembic/metadata sees them."""
from app.models.application import Application, ApplicationState
from app.models.application_event import ApplicationEvent
from app.models.generated_message import GeneratedMessage, MessageType
from app.models.job_opportunity import JobOpportunity, Modality
from app.models.profile import Profile, Seniority
from app.models.project import Project
from app.models.score import Recommendation, Score
from app.models.skill import Skill
from app.models.user import User

__all__ = [
    "Application",
    "ApplicationState",
    "ApplicationEvent",
    "GeneratedMessage",
    "MessageType",
    "JobOpportunity",
    "Modality",
    "Profile",
    "Seniority",
    "Project",
    "Recommendation",
    "Score",
    "Skill",
    "User",
]
