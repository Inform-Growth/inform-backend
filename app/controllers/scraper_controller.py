import os
from app.services.scraper_services.web_requests import WebRequestHandler
from app.services.scraper_services.url_ranking import URLRanker
from app.services.scraper_services.ai_data_collection import AIDataCollector
from app.services.scraper_services.document_handling import DocumentHandler
from app.services.do_spaces_service import DigitalOceanSpacesUploader
from bs4 import BeautifulSoup, SoupStrainer
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from app.models.scraper_models import URL, PageRanked, Page
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_openai import ChatOpenAI
from typing_extensions import Annotated, TypedDict
from langchain_core.runnables import RunnablePassthrough
from typing import List
from fastapi import HTTPException
import requests

from app.db.mongoengine_connection import MongoEngineConnection

db = MongoEngineConnection()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class PersonResponse(TypedDict):
    """A response containing a person."""

    name: str
    title: str 

class PeopleResponse(TypedDict):
    """A response containing a list of people."""

    people: List[PersonResponse]
    
class Summary(TypedDict):
    """A summary of a person."""
    summary: str    

class CompanyResponse(TypedDict):
    """A response containing a company."""

    name: str
    description: str

class StrategyResponse(TypedDict):
    """A response containing a strategy."""

    strategy: str



def get_filename_from_url(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.split('.')[-2]
    return domain

def run_scraper(args):
    company_description = args.get("company_description")
    url = args.get("url")
    email = args.get("email")
    llm = ChatOpenAI(model="gpt-4o-mini")
    try:
        web_handler = WebRequestHandler()
        ranker = URLRanker()
        ai_collector = AIDataCollector()
        doc_handler = DocumentHandler()
        print(f"Generating sitemap for {url}")
        pages_response = web_handler.parse_sitemap(url, url)

        favicon_url = web_handler.get_favicon(url)
        print(f"Ranking URLs for {url}")
        print(len(pages_response))
        if len(pages_response) == 0:
            raise Exception("Error: No pages found to generate strategy or too many pages in sitemap")
        ranked_urls = ranker.rank_urls(pages_response[:50])
        for page in ranked_urls:
            print(f"Page: {page.url} Company likelyhood: {page.company_likelyhood} People likelyhood: {page.people_likelyhood}")

        company_pages = [page for page in ranked_urls if page.company_likelyhood > 0.7]
        people_pages = [page for page in ranked_urls if page.people_likelyhood > 0.7]
        print(len(company_pages))
        print(len(people_pages))
        if company_pages == [] and people_pages == []:
            raise Exception("Error: Not enough information to generate strategy")
        print("ranking pages")
        ranked_pages = {page.url: page for page in company_pages + people_pages}.values()
        if ranked_pages is None or len(ranked_pages) == 0:
            raise Exception("Error: No pages found to generate strategy")

        urls = [page.url for page in ranked_pages]

        print("loading documents")
        loader = WebBaseLoader(
            web_paths=urls,
            bs_kwargs=dict(
                parse_only=SoupStrainer(
                    lambda tag, attrs: (
                        # Focus on tags that usually contain main content
                        tag in ["article", "main", "div", "section"]
                        # Exclude elements with common repetitive classes or IDs
                        and not any(
                            cls in attrs.get("class", [])
                            for cls in ["sidebar", "footer", "header", "nav", "menu", "advertisement", "widget"]
                        )
                        and attrs.get("id") not in ["footer", "header", "navbar", "sidebar"]
                    )
                )
            ),
        )
        
        docs = loader.load()
        print("removing duplicate content")
        documents = doc_handler.remove_duplicate_content(docs)
        print("splitting documents")
        print(len(documents))
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents=documents)
        print(len(splits))
        vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
        
        retriever = vectorstore.as_retriever()
        # 2. Incorporate the retriever into a question-answering chain.
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        # Our rag_chain_from_docs has the following changes:
        # - add `.with_structured_output` to the LLM;
        # - remove the output parser
        def schema_chain(schema):
            rag_chain_from_docs = (
                {
                    "input": lambda x: x["input"],
                    "context": lambda x: format_docs(x["context"]),
                }
                | prompt
                | llm.with_structured_output(schema)
            )
            return rag_chain_from_docs

        print("Creating chains")
        retrieve_docs = (lambda x: x["input"]) | retriever

        company_chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
            answer=schema_chain(CompanyResponse)
        )
        print("Fetching company information")
        company_response = company_chain.invoke({"input": "What company does this website belong to?"})

        print("Fetching people")
        chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
            answer=schema_chain(PeopleResponse)
        )
        people = chain.invoke({"input": f"What do the people at {company_response['answer']['name']} do?"})

        summary_chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
            answer=schema_chain(Summary)
        )
        appendix_urls = []
        for p in people['answer']['people']:

            summary_response = summary_chain.invoke({"input": f"What does {p['name']} do at {company_response['answer']['name']}?"})
            for u in summary_response['context']:
                if u.metadata['source'] not in appendix_urls:
                    appendix_urls.append(u.metadata['source'])
            p['summary'] = summary_response['answer']['summary']

        
        
        print("Generating strategy")
        strategy = ai_collector.generate_strategy(company_description, company_response['answer']['description'], people['answer']['people'])

        for c in company_response['context']:
            if c.metadata['source'] not in appendix_urls:
                appendix_urls.append(c.metadata['source'])
        filename = get_filename_from_url(url)
        print("Saving to markdown and converting to PDF")
        print(company_response['answer']['name'])
        print(people['answer']['people'])
        print(appendix_urls)
        print(strategy)
        

        doc_handler.save_to_markdown_and_convert_to_pdf(company_response['answer']['description'], strategy, people['answer']['people'], appendix_urls, filename + ".md", filename + ".pdf", favicon_url, company_response['answer']['name'])

        uploader = DigitalOceanSpacesUploader('inform')
        upload = uploader.upload_file(filename + ".pdf")
        os.remove(filename + ".pdf")
        print(upload)
        print("deleting vector store")
        vectorstore._client.delete_collection(vectorstore._collection.name)
        print(args.get("email"))
        print(args)
        response = {"message": "Strategy and report generated successfully", 
                    "url": "https://inform.sfo2.cdn.digitaloceanspaces.com/" +filename + ".pdf", 
                    "email": args.get("email"),
                    "company": company_response['answer']['name'],
                    "status": "success"}
        requests.post("https://hook.us1.make.com/3lbu58jf6zfd2rvktzkenwiqdghxw2ek", json=response)
        return response

    except Exception as e:
        response = {
            "message": str(e),
            "url": "",
            "company": "",
            "email": args.get("email"),
            "status": "error"
        }
        requests.post("https://hook.us1.make.com/3lbu58jf6zfd2rvktzkenwiqdghxw2ek", json=response)
        raise HTTPException(status_code=500, detail=str(e))