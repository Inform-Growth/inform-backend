from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List


class QuestionModel(BaseModel):
    question:str =  Field(..., description="The next form question")
    suggestions:List[str] = Field(..., description="Predicted answers for the next question")
