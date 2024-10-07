# url_ranking.py
from typing import List
# from langsmith import traceable
from langchain_openai import ChatOpenAI
from app.models.scraper_models import PageRanked,RankedPages
import os
from dotenv import load_dotenv
load_dotenv()


# Define your Pydantic models

class URLRanker:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name, temperature=0)

    def rank_urls(self, urls: List[str], batch_size: int = 20) -> List[PageRanked]:
        # print(os.getenv("OPENAI_API_KEY"))
        form_model = self.model.with_structured_output(RankedPages)
        ranked_urls = []
        len_urls = len(urls)
        print(f"Ranking {len_urls} URLs in batches of {batch_size}")
        for chunk in [urls[i:i + batch_size] for i in range(0, len_urls, batch_size)]:
            pages_string = "\n".join([f'{{"url": "{url}"}}' for url in chunk])
            find_form_prompt = f"""
            Out of the following urls, please rate the pages from 0 to 1 with the likelihood that the pages have information on what the company does and the people that work there.
            Respond in JSON format.
            If the url contains words like "about", "info", "company" or is the root page, it is very likely to have information on what the company does so give it a rating of 1.
            If the url contains words like "team", "people", "staff", "leadership", or a persons name like "john-doe" it is very likely to have information on the people that work there so give it a rating of 1.
            if the url contains words like "blog", "customers", "contact", "careers", "jobs", "case studies", "news", "events", "partners", it is very unlikely to have information on what the company does or the people that work there so give it a rating of 0.
            {pages_string}
            """
            urls_response = form_model.invoke(find_form_prompt)
            print(urls_response)
            ranked_urls.extend(urls_response.pages)
        return ranked_urls
