from typing import List, Optional
from pydantic import BaseModel, Field

class CheckResponse(BaseModel):
    """A response containing a check."""
    check: bool


class CompanySummaryResponse(BaseModel):
    name: str = Field(..., description="Company name")
    summary: str = Field(..., description="Company summary")
    mission: str = Field(..., description="Company mission statement")


class CompanyResponse(BaseModel):
    """Pydantic model for company response."""
    name: str
    description: str
    mission: str


class PageRanked(BaseModel):
    url: str = Field("", description="URL of the page")
    company_likelihood: float = Field(0.0, description="Likelihood of the page to have relevant information about the company from 0 to 1")
    people_likelihood: float = Field(0.0, description="Likelihood of the page to have relevant information about people from 0 to 1")


class Page(BaseModel):
    page_ranked: PageRanked
    title: Optional[str] = Field(None, description="Title of the page")
    html_content: Optional[str] = Field(None, description="Content of the page")
    content: Optional[str] = Field(None, description="The cleaned content of the page")


class PagesResponse(BaseModel):
    pages: List[Page] = Field("", description="List of pages with their URL and title")


class Person(BaseModel):
    name: str = Field("", description="Person's name")
    title: Optional[str] = Field("", description="Person's title")
    summary: Optional[str] = Field("", description="Brief summary about the person")
    # info: Optional[PersonInfo] = Field(None, description="Contact information of the person")


class PersonInfo(BaseModel):
    linkedin: Optional[str] = Field(None, description="URL to the person's LinkedIn profile")
    website: Optional[str] = Field(None, description="URL to the person's personal website")
    twitter: Optional[str] = Field(None, description="URL to the person's Twitter profile")
    phone: Optional[str] = Field(None, description="Phone number of the person")


class ContactResponse(BaseModel):
    people: List[Person] = Field(default_factory=list, description="List of people with detailed contact information")


class PeopleResponse(BaseModel):
    """Pydantic model for people response."""
    people: List[Person] = Field(default_factory=list, description="List of people with detailed contact information")


class RankedPages(BaseModel):
    pages: List[PageRanked] = Field(None, description="List of pages with their URL and ranking")


class StrategyPerson(BaseModel):
    name: str = Field("", description="Person's name")  # Set default to an empty string
    title: str = Field("", description="Person's title")  # Set default to an empty string
    summary: str = Field("", description="Brief summary about the person")  # Set default to an empty string
    info: Optional[PersonInfo] = Field(None, description="Contact information of the person")
    initial_message: str = Field("", description="Initial message to send to the person")  # Set default to an empty string


class StrategyRequest(BaseModel):
    company_description: str
    url: str


class StrategyResponse(BaseModel):
    strategy: str = Field(None, description="Sales strategy for the company in HTML format")


class Summary(BaseModel):
    """A summary of a person."""
    summary: str = Field("", description="A summary of the given context")


class SummaryResponse(BaseModel):
    """Pydantic model for summary response."""
    summary: str


class URL(BaseModel):
    url: str = Field("", description="URL of the page")


class SalesScraperRequestBody(BaseModel):
    """
    Class that is used to contain the information obtained from a post request from the sale scraper API.
    
    company_description: str
        The description of the company

    url: str
        The URL to scrape

    email: str
        The email to scrape
    """
    company_description: str = Field(..., description="The description of the company")
    url: str = Field(..., description="The URL to scrape")
    email: str = Field(..., description="The email to scrape")
    
    def __repr__(self):
        return (f"SalesScraperRequestBody(company_description='{self.company_description}', "
                f"url='{self.url}', email='{self.email}')")
    
    def __str__(self):
        return (f"SalesScraperRequestBody with company_description='{self.company_description}', "
                f"url='{self.url}', and email='{self.email}'")

class Scraper(BaseModel):
    """"
    Pydantic Model for the implementation of Scraper functionality
    """
    request_body: SalesScraperRequestBody = Field(..., description="The request body containing the company description, url and email")
    run_id: str | int = Field(..., description="The run ID generated in supabase of the scraper")