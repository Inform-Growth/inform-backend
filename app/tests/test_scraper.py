import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.controllers.scraper_controller import run_scraper
from app.models.scraper_models import SalesScraperRequestBody

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import the run_scraper function

from fastapi import HTTPException

@pytest.mark.asyncio
async def test_run_scraper_success():
    args = {
        "company_description": "We are a tech company focusing on AI solutions.",
        "url": "https://example.com",
        "email": "test@example.com"
    }
    
    scraper_request = SalesScraperRequestBody(**args)
    
    # Mock external dependencies
    with patch('app.scraper.WebRequestHandler') as mock_web_handler, \
         patch('app.scraper.URLRanker') as mock_ranker, \
         patch('app.scraper.AIDataCollector') as mock_ai_collector, \
         patch('app.scraper.DocumentHandler') as mock_doc_handler, \
         patch('app.scraper.DigitalOceanSpacesUploader') as mock_uploader_class, \
         patch('app.scraper.ChatOpenAI') as mock_chat_openai_class, \
         patch('app.scraper.db') as mock_db:

        # Mock instances
        mock_web_handler_instance = mock_web_handler.return_value
        mock_ranker_instance = mock_ranker.return_value
        mock_ai_collector_instance = mock_ai_collector.return_value
        mock_doc_handler_instance = mock_doc_handler.return_value
        mock_uploader_instance = mock_uploader_class.return_value
        mock_chat_openai_instance = mock_chat_openai_class.return_value

        # Set up return values and side effects for methods
        mock_web_handler_instance.parse_sitemap.return_value = ["https://example.com/about", "https://example.com/team"]
        mock_web_handler_instance.get_favicon.return_value = "https://example.com/favicon.ico"

        mock_ranker_instance.rank_urls.return_value = [
            MagicMock(url="https://example.com/about", company_likelyhood=0.9, people_likelyhood=0.1),
            MagicMock(url="https://example.com/team", company_likelyhood=0.1, people_likelyhood=0.9)
        ]

        # Mock DocumentHandler methods
        mock_doc_handler_instance.remove_duplicate_content.return_value = [MagicMock(page_content="About us content", metadata={"source": "https://example.com/about"})]
        mock_doc_handler_instance.save_to_markdown_and_convert_to_pdf.return_value = None

        # Mock AIDataCollector
        mock_ai_collector_instance.generate_strategy.return_value = "Generated strategy"

        # Mock uploader
        mock_uploader_instance.upload_file.return_value = {"url": "https://cdn.example.com/example.pdf"}

        # Mock ChatOpenAI
        mock_chat_openai_instance.return_value = '{"name": "Example Company", "description": "We are a tech company.", "mission": "Innovate AI solutions."}'

        # Call the run_scraper function
        response = await run_scraper("0",scraper_request)

        # Assert the response
        assert response["status"] == "success"
        assert "url" in response
        assert response["email"] == args["email"]
        assert response["company"] == "Example Company"

@pytest.mark.asyncio
async def test_run_scraper_failure():
    args = {
        "company_description": "We are a tech company focusing on AI solutions.",
        "url": "https://example.com",
        "email": "test@example.com"
    }
    
    scraper_request = SalesScraperRequestBody(**args)
    
    # Mock external dependencies to raise an exception
    with patch('app.scraper.WebRequestHandler') as mock_web_handler, \
         patch('app.scraper.requests.post') as mock_requests_post:

        mock_web_handler_instance = mock_web_handler.return_value
        mock_web_handler_instance.parse_sitemap.side_effect = Exception("Test exception")

        # Mock the requests.post to avoid actual HTTP requests during tests
        mock_requests_post.return_value = MagicMock(status_code=200)

        with pytest.raises(HTTPException) as exc_info:
            await run_scraper("0", scraper_request)

        assert exc_info.value.status_code == 500
        assert "Test exception" in str(exc_info.value.detail)
