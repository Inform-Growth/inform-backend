from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.submission_service import SubmissionService

router = APIRouter()

submission_service = SubmissionService()

class SubmissionRequestBody(BaseModel):
    form_id: str = Field(..., description="The ID of the form")
    context: dict = Field(..., description="The context of the submission")

class SubmissionResponseBody(BaseModel):
    response: str = Field(..., description="The response to the submission")

@router.post("/", response_model=dict)
async def handle_initial_submission(request_body: SubmissionRequestBody):
    form_id = request_body.form_id
    context = request_body.context
    result = submission_service.handle_initial_submission(form_id, context)
    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result

@router.post("/{id}", response_model=dict)
async def handle_submission_response(id: str, request_body: SubmissionResponseBody):
    response = request_body.response
    result = submission_service.handle_submission_response(id, response)
    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result
