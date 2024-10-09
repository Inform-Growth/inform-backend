import os
import json
from datetime import datetime

from app.services.scraper_services.web_requests import WebRequestHandler
from app.services.scraper_services.url_ranking import URLRanker
from app.services.scraper_services.ai_data_collection import AIDataCollector
from app.services.scraper_services.document_handling import DocumentHandler
from app.services.scraper_services.sales_qa_agent import SalesQAAgent
from app.services.do_spaces_service import DigitalOceanSpacesUploader
from bs4 import BeautifulSoup, SoupStrainer
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from app.models.scraper_models import CompanySummaryResponse, ContactResponse, Summary, CheckResponse, PageRanked
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, HTMLSectionSplitter
from typing_extensions import Annotated, TypedDict
from typing import List
from fastapi import HTTPException
import requests
from dotenv import load_dotenv
load_dotenv()

from app.db.s3 import S3Connection
from app.db.supabase_connection import SupabaseConnection
s3 = S3Connection()
db = SupabaseConnection()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)




def get_filename_from_url(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if len(domain_parts) >= 2:
        domain = domain_parts[-2]
    else:
        domain = parsed_url.netloc
    return domain

def get_pages(urls):
    loader = WebBaseLoader(
            web_paths=urls,
            bs_kwargs=dict(
                parse_only=SoupStrainer(
                    lambda tag, attrs: (
                        # Focus on tags that usually contain main content or links
                        tag in ["article", "main", "div", "section", "a", "h1", "h2", "h3", "h4", "h5", "h6"]
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
    return docs

# scraper_controller.py

async def run_scraper(args):
    company_description = args.get("company_description")
    url = args.get("url")
    run_id = args.get("run_id")
    try:
        db.update_sales_scraper_run(run_id=run_id, run_status="Started")
        # Initialize the agent
        filename = get_filename_from_url(url)
        agent = SalesQAAgent(collection_name=filename)
        ai_collector = AIDataCollector()
        doc_handler = DocumentHandler()

        # Initialize favicon_url
        favicon_url = None
        

        # Check if the embeddings (collection) already exist
        if agent.collection_exists() and len(agent.client.get_collection(agent.collection_name)) > 0:
            print("Embeddings for this URL already exist. Using cached embeddings.")
            agent.collection = agent.client.get_collection(agent.collection_name)
            # Get favicon_url
            web_handler = WebRequestHandler()
            favicon_url = web_handler.get_favicon(url)
        else:
            # Create a new collection
            print(f"Creating collection '{agent.collection_name}'.")
            if not agent.collection_exists():
                agent.collection = agent.client.create_collection(agent.collection_name, dimension=1536)
            else:
                agent.collection = agent.client.get_collection(agent.collection_name)
            print("Embeddings for this URL do not exist. Proceeding to scrape and store embeddings.")

            # Proceed with scraping and processing
            web_handler = WebRequestHandler()
            ranker = URLRanker()
            
            print(f"Generating sitemap for {url}")
            pages_response = web_handler.parse_sitemap(url, url)

            favicon_url = web_handler.get_favicon(url)
            print(f"Ranking URLs for {url}")
            
            if len(pages_response) == 0:
                raise Exception("Error: No pages found to generate strategy or too many pages in sitemap")

            # Extract urls based on keywords
            keyword_urls = []
            people_keywords = ["team", "people", "staff", "leadership", "executive", "management"]
            company_keywords = ["about", "info", "company", "home"]
            for page in pages_response:
                if any(keyword in page for keyword in people_keywords):
                    keyword_urls.append(PageRanked(url=page, company_likelyhood=0, people_likelyhood=1))
                if any(keyword in page for keyword in company_keywords):
                    keyword_urls.append(PageRanked(url=page, company_likelyhood=1, people_likelyhood=0))
            print(pages_response[:5])
            selected_urls = [url for url in pages_response if url not in people_keywords and url not in company_keywords][:80]
            # Get a subset starting from the 50th URL onward

            print(selected_urls[:80])
            ranked_urls = ranker.rank_urls(selected_urls, batch_size=20)

            # Extract relevant pages

            company_pages = [page for page in ranked_urls if page.company_likelyhood > 0.7]
            people_pages = [page for page in ranked_urls if page.people_likelyhood > 0.7]
            if not company_pages and not people_pages:
                raise Exception("Error: Not enough information to generate strategy")
            print("ranking pages")
            ranked_pages = {page.url: page for page in company_pages + people_pages + keyword_urls}
            if not ranked_pages:
                raise Exception("Error: No pages found to generate strategy")
            urls = list(ranked_pages.keys())
            print(urls)
            
            print("loading documents")
            docs = get_pages(urls)
            print("removing duplicate content")
            documents = doc_handler.remove_duplicate_content(docs)
            print("removing empty content")
            documents = [doc for doc in documents if doc.page_content.strip()]
            print("Storing documents")
            for doc in documents:
                # Check if 'source' exists in the document's metadata
                if "source" in doc.metadata:
                    source = doc.metadata["source"]
                    # Check if the source exists in ranked_pages
                    if source in ranked_pages:
                        # Safely update the metadata without overwriting the whole dictionary
                        doc.metadata.update({
                            "company_likelyhood": ranked_pages[source].company_likelyhood,
                            "people_likelyhood": ranked_pages[source].people_likelyhood
                        })
                        print(f"Updated metadata for doc with source {source}: {doc.metadata}")
                    else:
                        print(f"Source {source} not found in ranked_pages")
                else:
                    print(f"Document does not have 'source' in metadata: {doc}")

            # Print the metadata of the first document to check if it has been updated
            # print(documents[0])
            if "people_likelyhood" not in documents[0].metadata:
                print("No people likelihood")
                raise Exception("Error: No people likelihood found in documents")

            ret = db.store_documents(documents)
            print("splitting documents")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
            splits = text_splitter.split_documents(documents=documents)
            print(len(splits))
            # Deduplicate the splits
            unique_texts = set()
            unique_splits = []

            for doc in splits:
                text = doc.page_content.strip()
                if text not in unique_texts:
                    unique_texts.add(text)
                    unique_splits.append(doc)
                else:
                    print(f"Duplicate text found and skipped: {text[:30]}...")

            # Remove splits with content less than 100 characters
            unique_splits = [doc for doc in unique_splits if len(doc.page_content) > 100]

            print("Creating vecs client and storing embeddings")
            # Store embeddings
            agent.store_embeddings(unique_splits)

        # Proceed with the rest of the code using the agent and existing embeddings
        db.update_sales_scraper_run(run_id=run_id, run_status="Getting People Info")

        # Initialize appendix URLs list
        appendix_urls = []

        # Get company information
        print("Fetching company information")
        company_query = "What company does this website belong to?"
        company_context = agent.retrieve_documents(company_query, filters={"company_likelyhood": {"$gt": 0.7}})
        if not company_context:
            company_context = agent.retrieve_documents(company_query)
        
        company_response = agent.ask_question(
            query=company_query,
            response_model=CompanySummaryResponse,
            context_docs=company_context
        )
        if not company_response:
            raise Exception("Failed to retrieve company information.")

        # Collect appendix URLs from company context
        for doc in company_context:
            print(doc)
            if 'source' in doc[2] and doc[2]['source'] not in appendix_urls:
                appendix_urls.append(doc[2]['source'])

        # Get people information
        print("Fetching people")
        people_query = f"Who is on the {company_response.name} team?"
        people_context = agent.retrieve_documents(people_query, filters={"people_likelyhood": {"$gt": 0.7}})
        if not people_context:
            people_context = agent.retrieve_documents(people_query)
        people_response = agent.ask_question(
            query=people_query,
            response_model=ContactResponse,
            context_docs=people_context
        )
        print(people_response)
        if not people_response:
            people_response = ContactResponse(people=[])
        
        # Fetching summaries for people
        print("Fetching summaries for people")
        valid_people = []
        for person in people_response.people:
            # Check if the person is associated with the company
            check_query = f"Is {person.name} on the team at {company_response.name}?"
            check_context = agent.retrieve_documents(check_query, filters={"people_likelyhood": {"$gt": 0.7}})
            check_response = agent.ask_question(
                query=check_query,
                response_model=CheckResponse,
                context_docs=check_context
            )
            if not check_response or not check_response.check:
                continue

            # Get summary of the person
            summary_query = f"What does {person.name} do at {company_response.name}?"
            summary_context = agent.retrieve_documents(summary_query, filters={"people_likelyhood": {"$gt": 0.7}})
            summary_response = agent.ask_question(
                query=summary_query,
                response_model=Summary,
                context_docs=summary_context
            )
            if summary_response:
                person.summary = summary_response.summary

            valid_people.append(person)

            # Collect appendix URLs from summary context
            for doc in summary_context:
                if 'source' in doc[2] and doc[2]['source'] not in appendix_urls:
                    appendix_urls.append(doc[2]['source'])

        # Now you can proceed with generating the strategy and saving the report
        db.update_sales_scraper_run(run_id=run_id, run_status="Generating Strategy")
        print("Generating strategy")
        strategy = agent.generate_strategy(company_description, company_response, valid_people)

        # Proceed with saving to markdown, converting to PDF, uploading, etc.
        print("Saving to markdown and converting to PDF")
        print(valid_people)
        print(strategy)
        
        # Update filename with timestamp - solves crash!
        current_timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        filename = filename + current_timestamp
        
        db.update_sales_scraper_run(run_id=run_id, run_status="Generating PDF")
        await doc_handler.generate_html_and_convert_to_pdf(
            company_summary=company_response,
            strategy=strategy,
            people=valid_people,
            appendix_urls=appendix_urls,
            pdf_filename=filename+".pdf",
            favicon_url=favicon_url,
            company_name=company_response.name,
            mission=company_response.mission
        )
        
        uploader = DigitalOceanSpacesUploader('inform')
        upload = uploader.upload_file(filename + ".pdf")
        s3.upload_file(filename + ".pdf")
        
        print(upload)
        # Optionally delete the collection if not needed
        # collection.delete()
        print(args.get("email"))
        print(args)
        response = {
            "message": "Strategy and report generated successfully", 
            "url": f"https://inform.sfo2.cdn.digitaloceanspaces.com/{filename}.pdf",
            "email": args.get("email"),
            "filename": filename,
            "company": company_response.name,
            "status": "success"
        }
        requests.post("https://hook.us1.make.com/3lbu58jf6zfd2rvktzkenwiqdghxw2ek", json=response)
        db.update_sales_scraper_run(run_id=run_id, run_results={"strategy": strategy}, run_status="Success")
        os.remove(filename + ".pdf")
        return response

    except Exception as e:
        db.update_sales_scraper_run(run_id=run_id, run_results=str(e), run_status="Error")
        response = {
            "message": str(e),
            "url": "",
            "company": "",
            "email": args.get("email"),
            "status": "error"
        }
        requests.post("https://hook.us1.make.com/3lbu58jf6zfd2rvktzkenwiqdghxw2ek", json=response)
        raise HTTPException(status_code=500, detail=str(e))
