# ai_data_collection.py

from typing import List, Tuple
import langchain
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter,HTMLSectionSplitter

from typing import List
import html2text
from app.models.scraper_models import CompanySummaryResponse, ContactResponse, StrategyResponse
from dotenv import load_dotenv
load_dotenv()



class AIDataCollector:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = OpenAI(model=model_name, temperature=0.2, max_tokens=-1)
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
        strategy_model = self.model
        selling_people = '\n\n'.join([f"{person.name} - {person.title}\n {person.summary}" for person in people_info])
        strategy_prompt = f"""
            You are a sales strategist with a deep understanding of highly targeted, personalized sales strategies. Based only on the information provided below, craft a comprehensive and detailed sales strategy, emphasizing personalized messaging, the buyer’s specific pain points, and the unique value proposition that addresses their needs.

            Your response should include:
            1. **Overview of the target company's potential business needs, including industry context, common challenges, and relevant trends. (Consider elements like funding status, market competition, or technological advancements).

            2. **Tailored initial messaging for each role in the decision-making chain (e.g., CEO, CFO, Head of Sales, CTO). Each message should address the person’s specific responsibilities, priorities, pain points, and goals within the company.

            3. **A conversation script that outlines how to probe for needs and steer the conversation based on buyer responses. The script should include:

                - **Open-ended probing questions based on role-specific pain points.
                - **Strategies for active listening and emotional engagement.
                - **Techniques to categorize the conversation into one of the following: "Active Lead," "Objection," "Not Interested," "Bad Timing," or "Bad Fit."
            4. **Resolution strategies for objections (e.g., budget, urgency, prior negative experiences) based on common objections in the industry.

            5. **Follow-up actions for each lead category, including appropriate timelines and messaging for nurturing leads, overcoming objections, or re-engaging potential buyers after an initial conversation.

            Your company summary:
            {company_description}

            The company you are selling to: 
            {sales_company_summary}

            The people you are selling to:
            {selling_people}

            Please provide a fully structured and cleanly formatted HTML response, ensuring proper use of tags such as `<h2>`, `<p>`, `<ul>`, and `<strong>` where appropriate to enhance readability. Do not use new line characters or markdown syntax in your response.
            """
        print(strategy_prompt)
        strategy = strategy_model.invoke(strategy_prompt)
        print(strategy)
        return strategy_model.invoke(strategy_prompt)
    def html_to_markdown(self, html_content):
        h = html2text.HTML2Text()
        h.ignore_links = True
        return h.handle(html_content)
