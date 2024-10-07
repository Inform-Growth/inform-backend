from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from app.db.supabase_connection import SupabaseConnection
from app.controllers.scraper_controller import run_scraper


router = APIRouter()
db = SupabaseConnection()

class SalesScraperRequestBody(BaseModel):
    company_description: str = Field(..., description="The description of the company")
    url: str = Field(..., description="The URL to scrape")
    email: str = Field(..., description="The email to scrape")

@router.post("/", response_model=dict)
async def handle_sales_scraper_request(request_body: SalesScraperRequestBody, background_tasks: BackgroundTasks):
    company_description = request_body.company_description
    url = request_body.url
    email = request_body.email

    # Step 1: Create the scraper run in the database and set its status to "Pending"
    run = db.create_sales_scraper_run(email=email, description=company_description, url=url)
    run_id = run["id"]

    # Step 2: Immediately return the run_id to the client
    response = {"run_id": run_id, "message": "Scraper run has been created and is processing in the background."}
    
    # Step 3: Add the long-running scraper task to background tasks
    background_tasks.add_task(process_scraper_run, run_id, company_description, url, email)
    
    return response


async def process_scraper_run(run_id: str, company_description: str, url: str, email: str):
    """
    This function will be run in the background and process the long-running scraping task.
    """
    try:
        # Step 4: Update the scraper run status to 'Started'
        db.update_sales_scraper_run(run_id=run_id, run_status="Started")

        # Run the scraper asynchronously
        result = await run_scraper({"company_description": company_description, "url": url, "email": email, "run_id": run_id})

        # Step 5: If the scraper runs successfully, update the status to 'Success'
        db.update_sales_scraper_run(run_id=run_id, run_results=result, run_status="Success")
    
    except Exception as e:
        # Step 6: If an error occurs, update the status to 'Error'
        db.update_sales_scraper_run(run_id=run_id, run_results=str(e), run_status="Error")
        raise e
