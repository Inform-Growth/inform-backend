from typing import List, Optional
from langchain_core.pydantic_v1 import Field, BaseModel


# Define your Pydantic models
class URL(BaseModel):
    url: str = Field("", description="URL of the page")

class PageRanked(BaseModel):
    url: str = Field("", description="URL of the page")
    company_likelyhood: float = Field(0.0, description="Likelyhood of the page to have relevant information about the company from 0 to 1")
    people_likelyhood: float = Field(0.0, description="Likelyhood of the page to have relevant information about people from 0 to 1")
class RankedPages(BaseModel):
    pages: List[PageRanked] = Field(None, description="List of pages with their URL and ranking")

class Page(BaseModel):
    page_ranked: PageRanked
    title: Optional[str] = Field(None, description="Title of the page")
    html_content: Optional[str] = Field(None, description="Content of the page")
    content: Optional[str] = Field(None, description="The cleaned content of the page")

class PagesResponse(BaseModel):
    pages: List[Page] = Field("", description="List of pages with their URL and title")

class CompanySummaryResponse(BaseModel):
    name: str = Field(..., description="Company name")
    summary: str = Field(..., description="Company summary")
    mission: str = Field(..., description="Company mission statement")
    products: List[str] = Field(default_factory=list, description="List of company products or services")

class PersonInfo(BaseModel):
    linkedin: Optional[str] = Field(None, description="URL to the person's LinkedIn profile")
    website: Optional[str] = Field(None, description="URL to the person's personal website")
    twitter: Optional[str] = Field(None, description="URL to the person's Twitter profile")
    phone: Optional[str] = Field(None, description="Phone number of the person")

class Person(BaseModel):
    name: str = Field("", description="Person's name")
    title: Optional[str] = Field("", description="Person's title")
    summary: str = Field("", description="Brief summary about the person")
    info: Optional[PersonInfo] = Field(None, description="Contact information of the person")

class ContactResponse(BaseModel):
    people: List[Person] = Field(default_factory=list, description="List of people with detailed contact information")

class StrategyPerson(BaseModel):
    name: str = Field("", description="Person's name")  # Set default to an empty string
    title: str = Field("", description="Person's title")  # Set default to an empty string
    summary: str = Field("", description="Brief summary about the person")  # Set default to an empty string
    info: Optional[PersonInfo] = Field(None, description="Contact information of the person")
    initial_message: str = Field("", description="Initial message to send to the person")  # Set default to an empty string


class StrategyResponse(BaseModel):
    strategy: str = Field("", description="Sales strategy for the company")

class StrategyRequest(BaseModel):
    company_description: str
    url: str