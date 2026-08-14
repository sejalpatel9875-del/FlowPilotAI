from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    title: str
    clientName: str
    status: str = "in_progress"
    deadline: str
    progressPercent: int = 0
    hourlyRate: float = 100.0


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
