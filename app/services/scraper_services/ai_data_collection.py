# ai_data_collection.py

from typing import List, Tuple
import langchain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter,HTMLSectionSplitter

from typing import List
import html2text
from app.models.scraper_models import CompanySummaryResponse, ContactResponse, StrategyResponse



class AIDataCollector:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name)
        self.embeddings_model = OpenAIEmbeddings()
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        self.recursive_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, chunk_overlap=64, length_function=len
        )
        self.html_text_splitter = HTMLSectionSplitter(headers_to_split_on=headers_to_split_on)

    def get_context_from_query(self, query, db) -> Tuple[str, List[str]]:
        similarity_scores = db.similarity_search(query)
        urls = [x.metadata['url'] for x in similarity_scores]
        top_chunks = [x.page_content for x in similarity_scores]
        return "\n".join(top_chunks), urls

    def get_company_summary(self, context: str) -> CompanySummaryResponse:
        summary_model = self.model.with_structured_output(CompanySummaryResponse)
        summary_prompt = f"""
        Relevant information:
        {context}
        Based only on the relevant information, extract a brief summary of the company, its mission, and optionally list main products/services offered. Use only information included in the context.
        """
        return summary_model.invoke(summary_prompt)

    def get_people_info(self, query_context: str) -> ContactResponse:
        people_model = self.model.with_structured_output(ContactResponse)
        people_prompt = f"""
        Page context: {query_context}
        Based only on the page context, find all of the people listed on the page and return them in JSON format.
        """
        return people_model.invoke(people_prompt)

    def generate_strategy(self, company_description: str, sales_company_summary: str, people_info: str) -> StrategyResponse:
        strategy_model = self.model.with_structured_output(StrategyResponse)
        strategy_prompt = f"""
        You are a sales expert who creates highly targetes and personalized sales strategies.
        Based only on the on the following information, please generate a targeted stales strategy focusing on the best messaging to use for you to sell to the target company and its people.
        Your company summary:
        {company_description}

        The company you are selling to: 
        {sales_company_summary}

        The people you are selling to:
        {people_info}

        Respond in markdown format.
        """
        print(strategy_prompt)
        return strategy_model.invoke(strategy_prompt)
    def html_to_markdown(self, html_content):
        h = html2text.HTML2Text()
        h.ignore_links = True
        return h.handle(html_content)
