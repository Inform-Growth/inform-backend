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
@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

@app.get("/")
def root():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Please respond to the user's request only based on the given context."),
        ("user", "Question: {question}\nContext: {context}")
    ])
    model = ChatOpenAI(model="gpt-3.5-turbo")
    output_parser = StrOutputParser()

    chain = prompt | model | output_parser

    question = "Can you summarize this morning's meetings?"
    context = "During this morning's meeting, we solved all world conflict."
    res = chain.invoke({"question": question, "context": context})
    return res

@app.get("/upload")
def upload():
    uploader = DigitalOceanSpacesUploader('inform')
    upload = uploader.upload_file("citycapitalventures.pdf")
    print(upload)
    return "Uploaded"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)