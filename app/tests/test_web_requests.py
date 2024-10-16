# test_web_requests.py
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.scraper_services.web_requests import WebRequestHandler

def test_parse_sitemap():
    handler = WebRequestHandler()
    url = "https://example.com"

    with patch('app.services.scraper_services.web_requests.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<urlset><url><loc>https://example.com/about</loc></url></urlset>"
        mock_get.return_value = mock_response

        sitemap_urls = handler.parse_sitemap(url, url)
        assert sitemap_urls == ["https://example.com/about"]
