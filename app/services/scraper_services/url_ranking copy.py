# url_ranking.py
from typing import List
from langchain_openai import ChatOpenAI,OpenAI
from app.models.scraper_models import PageRanked,RankedPages
from langchain.output_parsers import (
    RetryOutputParser,
    PydanticOutputParser,
)
from langchain_core.prompts import (
    PromptTemplate,
)
from langchain_core.runnables import RunnableLambda, RunnableParallel

# Define your Pydantic models

class URLRanker:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name, temperature=0)
        parser = PydanticOutputParser(pydantic_object=RankedPages)
        retry_parser = RetryOutputParser.from_llm(parser=parser, llm=OpenAI(temperature=0))
        self.template = PromptTemplate(
            template="Out of the following pages, please rate the pages from 0 to 1 with the likelihood that the pages have information on what the company does and the people that work there.\nURLS: {urls} \n Ranked URLs:",
            input_fields=["urls"],
            partial_variables={"format_instructions": parser.get_format_instructions()})
        self.completion_chain = self.template | self.model
        self.chain = RunnableParallel(
            completion=self.completion_chain, prompt_value=self.template, 
        ) | RunnableLambda(lambda x: retry_parser.parse_with_prompt(**x))

    def rank_urls(self, urls: List[str], batch_size: int = 20) -> List[PageRanked]:
        # form_model = self.model.with_structured_output(RankedPages)
        ranked_urls = []
        len_urls = len(urls)
        print(f"Ranking {len_urls} URLs in batches of {batch_size}")
        # logger.info(f"Ranking {len_urls} URLs in batches of {batch_size}")
        for chunk in [urls[i:i + batch_size] for i in range(0, len_urls, batch_size)]:
            print(f"Ranking chunk of {len(chunk)} URLs")
            pages_string = "\n".join([f'{{"url": "{url}"}}' for url in chunk])
            # find_form_prompt = f"""
            # Out of the following pages, please rate the pages from 0 to 1 with the likelihood that the pages have information on what the company does and the people that work there.
            # Respond in JSON format.
            # {pages_string}
            # """
            urls_response = self.chain.invoke({"urls": pages_string})
            ranked_urls.extend(urls_response.pages)
        return ranked_urls
