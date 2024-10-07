import os
import sys

print("Current working directory:", os.getcwd())
sys.path.append(os.getcwd())
from fastapi import FastAPI
from app.api.api_v1.endpoints import submission
from app.api.api_v1.endpoints import form
from app.api.api_v1.endpoints import salesscraper
import os
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
import uvicorn
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.do_spaces_service import DigitalOceanSpacesUploader
from dotenv import load_dotenv
load_dotenv()
from app.services.scraper_services.document_handling import DocumentHandler
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


app.include_router(submission.router, prefix="/api/v1/submission", tags=["submission"])
app.include_router(form.router, prefix="/api/v1/form", tags=["form"])
app.include_router(salesscraper.router, prefix="/api/v1/sales-scraper", tags=["sales-scraper"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)