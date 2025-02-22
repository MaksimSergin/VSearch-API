from pydantic import BaseModel, Field

class VacancyInput(BaseModel):
    text: str = Field(..., description="Vacancy text")
    source: str = Field(..., description="Source of the vacancy")
