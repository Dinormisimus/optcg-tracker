from pydantic import BaseModel, Field

class LeaderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=20)
    color: str = Field(min_length=1, max_length=50)

class LeaderResponse(BaseModel):
    id: int
    name: str
    code: str
    color: str

    model_config = {"from_attributes": True}  # Prema Predavanju 5 (slajd 40)