from pydantic import BaseModel, ConfigDict

class LeaderResponse(BaseModel):
    id: int
    name: str
    code: str
    color: str

    model_config = ConfigDict(from_attributes=True)