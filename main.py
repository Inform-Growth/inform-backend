import os
import sys
from fastapi import FastAPI, HTTPException
from pyppeteer import launch
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
import uvicorn
from dotenv import load_dotenv
#from app.api.api_v1.endpoints import submission
#from app.api.api_v1.endpoints import form
from app.api.api_v1.endpoints import salesscraper

print("Current working directory:", os.getcwd())
sys.path.append(os.getcwd())

load_dotenv()

sentry_sdk.init(
    dsn="https://530ac3a2e8affdf6de10b9ba2f7ac1b4@o4507560294088704.ingest.us.sentry.io/4507560295923712",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#app.include_router(submission.router, prefix="/api/v1/submission", tags=["submission"])
#app.include_router(form.router, prefix="/api/v1/form", tags=["form"])
app.include_router(salesscraper.router, prefix="/api/v1/sales-scraper", tags=["sales-scraper"])

async def generate_pdf(url: str, output_path: str):
    try:
        print("Launching browser")
        browser = await launch(headless=True, 
                               executablePath='/usr/bin/chromium',
                               args=[
                                '--no-sandbox',
                                '--disable-setuid-sandbox',
                                '--disable-dev-shm-usage',   # Helps reduce memory issues in Docker
                                '--disable-gpu',              # GPU rendering is not supported in headless mode in Docker
                                '--disable-software-rasterizer'
                            ])
        page = await browser.newPage()
        print(f"Navigating to {url}")
        await page.goto(url)
        print(f"Generating PDF at {output_path}")
        await page.pdf({'path': output_path})
        await browser.close()
        print("PDF generation completed")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise

@app.post("/generate-pdf/")
async def generate_pdf_endpoint(body: dict):
    url = body.get("url")
    output_path = "output.pdf"
    try:
        await generate_pdf(url, output_path)
        return {"message": "PDF generated successfully"}
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")