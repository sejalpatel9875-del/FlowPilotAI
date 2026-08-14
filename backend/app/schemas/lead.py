from pydantic import BaseModel, ConfigDict


class LeadBase(BaseModel):
    name: str
    company: str
    email: str
    value: float = 0.0
    score: int = 50
    status: str = "new"
    source: str = "Organic"


class LeadCreate(LeadBase):
    pass


class LeadResponse(LeadBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
