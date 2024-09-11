import json
from dataclasses import dataclass, field
from utils.mongodb import MongoEngineConnection

from fastapi import FastAPI, HTTPException, Response
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mongodb = MongoEngineConnection()


@app.get("/")
def read_root() -> Response:
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
