from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field
from app.db.mongoengine_connection import MongoEngineConnection
from app.controllers.scraper_controller import run_scraper


router = APIRouter()
db = MongoEngineConnection()

class SalesScraperRequestBody(BaseModel):
    company_description: str = Field(..., description="The description of the company")
    url: str = Field(..., description="The URL to scrape")
    email: str = Field(..., description="The email to scrape")

@router.post("/", response_model=dict)
async def handle_sales_scraper_request(request_body: SalesScraperRequestBody):
    company_description = request_body.company_description
    url = request_body.url
    email = request_body.email
    run = db.create_sales_scraper_run(email=email, description=company_description, url=url)
    print(run.id)
    print(f"url: {url}")
    result = run_scraper({"company_description": company_description, "url": url, "email": email})
    if "Error" in result:
        print("Error in result")
        db.update_sales_scraper_run(run_id=run.id, run_results=result, run_status="Error")
        raise HTTPException(status_code=400, detail=result)
    else:
        db.update_sales_scraper_run(run_id=run.id, run_results=result, run_status="Success")
    return result
