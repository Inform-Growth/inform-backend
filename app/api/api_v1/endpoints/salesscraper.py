from typing import Any
from fastapi import APIRouter, BackgroundTasks
from app.controllers.scraper_controller import run_scraper
from app.db.supabase_connection import SupabaseConnection
from app.models.scraper_models import SalesScraperRequestBody

router = APIRouter()
db = SupabaseConnection()


@router.post("/", response_model=dict)
async def handle_sales_scraper_request(request_body: SalesScraperRequestBody,
                                       background_tasks: BackgroundTasks) -> Any:
	"""
    Handles the sales scraper request, initiating the scraper run and adding the task to background tasks.

    Parameters:
    request_body (SalesScraperRequestBody): The request body containing the necessary details to run the scraper.
    background_tasks (BackgroundTasks): The background tasks manager for running tasks asynchronously.

    Returns:
    dict: Contains the run_id and a message regarding the status of the scraper run initiation.
    """
	if request_body is None:
		print("Request body is empty! No scraper operation will be performed.")
		return None
	
	# Step 1: Create the scraper run in the database and immediately return the run_id to the client.
	run_id = _create_scraper_run(request_body.email, request_body.company_description, request_body.url)
	
	# Step 2: Set scraper status to "Pending" if a valid run_id was returned.
	if run_id is not None:
		db.update_sales_scraper_run(run_id=run_id, run_status="Pending")
	else:
		print("Error! Run_ID is not valid, so no valid scraper was created.")
	
	# Step 3: Add the long-running scraper task to background tasks
	background_tasks.add_task(process_scraper_run, run_id, request_body)
	
	return {"run_id": run_id, "message": "Scraper run has been created and is processing in the background."}


def _create_scraper_run(email: str, description: str, url: str) -> Any | None:
	"""
	Creates a new scraper run and returns its unique identifier.

	Parameters:
	email (str): The email associated with the scraper run.
	description (str): A brief description of the scraper run.
	url (str): The URL to be scraped.

	Returns:
	Any | None: The unique identifier of the created scraper run if successful, otherwise None.
	"""
	run = db.create_sales_scraper_run(email=email, description=description, url=url)
	return run["id"]


async def process_scraper_run(database_run_id: str, request_body: SalesScraperRequestBody):
	"""
	This function will be run in the background and process the long-running scraping task.

	Parameters:
	database_run_id (str): The unique identifier of the scraper run in the database.
	request_body (SalesScraperRequestBody): The request body containing the necessary details to run the scraper.
	"""
	try:
		# Step 4: Update the scraper run status to 'Started'
		db.update_sales_scraper_run(run_id=database_run_id, run_status="Started")
		
		# Run the scraper asynchronously
		result = await run_scraper(database_run_id, request_body)
		
		# Step 5: If the scraper runs successfully, update the status to 'Success'
		db.update_sales_scraper_run(run_id=database_run_id, run_results=result, run_status="Success")
	
	except Exception as e:
		# Step 6: If an error occurs, update the status to 'Error'
		db.update_sales_scraper_run(run_id=database_run_id, run_results=str(e), run_status="Error")
		print(f"An error occurred during scraping: {e}")
		raise e
