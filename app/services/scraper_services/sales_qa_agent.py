# sales_qa_agent.py

import os
import json
from typing import List, Optional, Tuple
from pydantic import BaseModel, ValidationError
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import vecs
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, ValidationError


from dotenv import load_dotenv
load_dotenv()


class CompanyResponse(BaseModel):
    """Pydantic model for company response."""
    name: str
    description: str
    mission: str

class Person(BaseModel):
    """Pydantic model for a person."""
    name: str
    title: Optional[str] = None
    summary: Optional[str] = None

class PeopleResponse(BaseModel):
    """Pydantic model for people response."""
    people: List[Person]

class CheckResponse(BaseModel):
    """Pydantic model for check response."""
    check: bool

class SummaryResponse(BaseModel):
    """Pydantic model for summary response."""
    summary: str

class StrategyResponse(BaseModel):
    """Pydantic model for strategy response."""
    strategy: str

class SalesQAAgent:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        # Initialize vecs client
        DB_CONNECTION = os.getenv("SUPABASE_URI")  # PostgreSQL connection string
        if not DB_CONNECTION:
            raise ValueError("DB_CONNECTION environment variable is not set.")
        self.client = vecs.Client(DB_CONNECTION)

        # if self.collection_exists():
        #     self.collection = self.client.get_collection(self.collection_name)
        # else:
        #     # Create a new collection
        #     print(f"Creating collection '{collection_name}'.")
        #     self.collection = self.client.create_collection(self.collection_name, dimension=1536)
        # Initialize the embedding model
        self.embedding_model = OpenAIEmbeddings()

        # Initialize the LLM with function calling capabilities
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    def collection_exists(self):
        print([x.name for x in self.client.list_collections()])
        return self.collection_name in [x.name for x in self.client.list_collections()]

    def store_embeddings(self, splits):
        """Stores embeddings into the vecs collection."""
        texts = [doc.page_content for doc in splits]
        embeddings = self.embedding_model.embed_documents(texts)

        records = []
        for i, text in enumerate(texts):
            embedding = embeddings[i]
            metadata = splits[i].metadata
            record = {
                "id": f"doc_{i}",  # Ensure unique ID for each record
                "value": text,
                "embedding": embedding,
                "metadata": metadata
            }
            records.append((text, embedding, metadata))
            # records.append(record)
        # TEST: if records ae empty 
        # Upsert the embeddings into the collection
        self.collection.upsert(records=records)
        # Create an index if not already created
        self.collection.create_index()

    def retrieve_documents(self, query: str, filters=None, top_k: int = 5) -> List[dict]:
        """Retrieves documents relevant to the query."""
        query_embedding = self.embedding_model.embed_query(query)

        # Query the collection
        results = self.collection.query(
            data=query_embedding,
            limit=top_k,
            include_value=True,
            include_metadata=True,
            filters=filters
        )

        # results is a list of dictionaries with keys: 'id', 'score', 'value', 'metadata'
        return results

    def ask_question(self, query: str, response_model: BaseModel, context_docs: List[dict]):
        """Asks the LLM a question and ensures the response matches the Pydantic model."""
        # Create the output parser
        output_parser = PydanticOutputParser(pydantic_object=response_model)

        # Create the prompt
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an assistant for question-answering tasks. "
                    "Use the following pieces of retrieved context to answer "
                    "the question. If you don't know the answer, say that you "
                    "don't know. Use three sentences maximum and keep the "
                    "answer concise."
                ),
                (
                    "human",
                    "Context:\n{context}\n\n"
                    "Question:\n{question}\n\n"
                    "Provide the answer in the following JSON format:\n"
                    "{format_instructions}"
                ),
            ]
        )

        # Get the format instructions from the output parser
        format_instructions = output_parser.get_format_instructions()

        # Extract texts from context_docs
        print(context_docs[0])
        print(context_docs[0][0])
        context_texts = [doc[0] for doc in context_docs]

        # Format the prompt
        prompt = prompt_template.format_messages(
            context='\n\n'.join(context_texts),
            question=query,
            format_instructions=format_instructions
        )
        # print(prompt)
        # Call the LLM
        response = self.llm.invoke(prompt)

        # Parse the output
        try:
            parsed_output = output_parser.parse(response.content)
            print(parsed_output)
            return parsed_output
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Failed to parse response for query '{query}': {e}")

            # Use the OutputFixingParser to fix the output
            fixing_parser = OutputFixingParser.from_llm(parser=output_parser, llm=self.llm)
            try:
                fixed_output = fixing_parser.parse(response.content)
                return fixed_output
            except Exception as fix_error:
                print(f"Failed to fix the output: {fix_error}")
                return None

    def get_company_info(self):
        """Retrieves company information."""
        company_query = "What company does this website belong to?"
        company_context = self.retrieve_documents(company_query)
        company_response = self.ask_question(
            query=company_query,
            response_model=CompanyResponse,
            context_docs=company_context
        )
        return company_response, company_context  # Return context for later use

    def get_people_info(self, company_name: str):
        """Retrieves information about people at the company."""
        people_query = f"Who are the people at {company_name}?"
        people_context = self.retrieve_documents(people_query)
        people_response = self.ask_question(
            query=people_query,
            response_model=PeopleResponse,
            context_docs=people_context
        )
        return people_response, people_context  # Return context for later use

    def check_person(self, person_name: str, company_name: str):
        """Checks if a person is associated with the company."""
        check_query = f"Is {person_name} a person at {company_name}?"
        check_context = self.retrieve_documents(check_query)
        check_response = self.ask_question(
            query=check_query,
            response_model=CheckResponse,
            context_docs=check_context
        )
        return check_response, check_context  # Return context for later use

    def get_person_summary(self, person_name: str, company_name: str):
        """Gets a summary of what a person does at the company."""
        summary_query = f"What does {person_name} do at {company_name}?"
        summary_context = self.retrieve_documents(summary_query)
        summary_response = self.ask_question(
            query=summary_query,
            response_model=SummaryResponse,
            context_docs=summary_context
        )
        return summary_response, summary_context  # Return context for later use
    
    def generate_strategy(self, company_description: str, sales_company_summary: str, people_info: List[dict]):
        """Generates a sales strategy based on the company information."""
        output_parser = PydanticOutputParser(pydantic_object=StrategyResponse)

        # Create the prompt
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a top-tier sales strategist known for creating innovative, highly effective sales strategies. Based on the information provided below, develop a unique and valuable sales strategy that addresses the buyer's specific needs and pain points. Your strategy should follow this exact structure:

                    Market Analysis

                    Industry trends and challenges
                    Competitive landscape
                    Target company opportunities


                    Personalized Sales Approach

                    Product/service focus and target audience
                    Value proposition and pain point solutions
                    Tailored conversation guide (opening, probing, presenting, closing)


                    Multi-Channel Strategy

                    Channel integration plan
                    Technology-enabled personalization


                    Implementation Plan

                    Key performance indicators (KPIs)
                    Timeline with major milestones


                    Innovation and Risk Management

                    Unconventional tactics and cutting-edge technology use
                    Potential challenges and mitigation strategiesle maintaining clarity and focus throughout each section.
                    """
                ),
                (
                    "human",
                    """My company summary:
            {company_desc}

            The company I am selling to: 
            {sales_company}

            The people I am selling to:
            {people}

            Please provide a fully structured and cleanly formatted HTML snippet (no head, body, footer tags, etc.) as the summary, ensuring proper use of tags such as `<h2>`, `<p>`, `<ul>`, and `<strong>` where appropriate to enhance readability. Do not use new line characters or markdown syntax in your response.
            """
                ),
            ]
        )

        # Get the format instructions from the output parser
        # format_instructions = output_parser.get_format_instructions()
        prompt = prompt_template.format_messages(
            company_desc=company_description,
            sales_company=sales_company_summary,
            people='\n\n'.join([f"{person.name} - {person.title}\n {person.summary}" for person in people_info]),
        )
        # print(prompt)
        # Call the LLM
        response = self.llm.invoke(prompt)

        return response.content