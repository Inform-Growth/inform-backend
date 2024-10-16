# sales_qa_agent.py
import json
import os
from typing import List, Type

import vecs
from dotenv import load_dotenv
from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, ValidationError

from app.models.scraper_models import CompanyResponse, CheckResponse, SummaryResponse, StrategyResponse, PeopleResponse

load_dotenv()


class SalesQAAgent:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        # Initialize vecs client
        DB_CONNECTION = os.getenv("SUPABASE_URI")  # PostgresSQL connection string
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

    def ask_question(self, query: str, response_model: Type[BaseModel], context_docs: List[dict]):
        """Asks the LLM a question and ensures the response matches the Pydantic model."""
        # Create the output parser
        output_parser = PydanticOutputParser(pydantic_object=response_model)
        
        # Create the prompt
        prompt_template = ChatPromptTemplate(
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
        print("context_docs")
        if len(context_docs) > 0:
            print(context_docs[0])
            print(context_docs[0][0])
            context_texts = [doc[0] for doc in context_docs]
        else:
            print("context_docs is empty")
            context_texts = []

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
        prompt_template = ChatPromptTemplate([
                (
                    "system",
                    """
                    As a top-tier sales strategist, create an innovative and highly effective sales strategy tailored to the specific company and industry information provided below.
                    
                    Your strategy should address the buyer's unique needs and pain points, following this structure:

                    1. Market Analysis
                    
                       a. Industry trends and challenges
                          - Key market dynamics and emerging technologies
                          - Regulatory environment
                    
                       b. Competitive landscape
                          - Major players and their market positions
                          - Recent significant industry developments
                    
                       c. Target company opportunities
                          - Current market position and potential growth areas
                    
                    2. Stakeholder Engagement
                    
                       a. Identify the three highest-ranking decision-makers from the provided data.
                    
                       b. For each of these three key stakeholders, craft a personalized opener message.
                       
                       c. Limit each opener to 2-3 sentences, ensuring it's concise yet impactful.
                       
                       Example structure for each opener:
                       "[Name], [Company]'s [Title], I've identified an opportunity to [brief value proposition] that aligns with [assumed priority based on their role]."
                    
                    3. Pain Point Identification
                    
                       a. Company-specific challenges
                          - Operational inefficiencies or market pressures
                    
                       b. Industry-wide issues relevant to the company
                    
                       c. Stakeholder-specific concerns
                          - Link to larger company objectives
                    
                    4. Solution-Focused Pitch
                    
                       a. Customized value proposition
                          - How your solution addresses identified pain points
                          - Quantifiable benefits
                    
                       b. Implementation roadmap
                          - Phased approach with quick wins and long-term advantages
                    
                       c. Relevant case studies
                          - Emphasize measurable outcomes and ROI
                    
                    5. Objection Handling
                    
                       a. Anticipate common objections
                          - Budget, implementation challenges, change resistance
                    
                       b. Prepared responses
                          - Data-driven counterarguments
                          - Flexible options or pilot programs
                    
                       c. Risk assessment and mitigation strategies
                    
                    Develop a highly personalized approach demonstrating deep understanding of the target company's unique position and objectives.
                    Use specific data points and industry terminology to establish expertise. Present a compelling, tailor-made solution that positions your offering as essential to the company's future success.
                    
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
        ])

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