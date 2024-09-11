# web_requests.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class WebRequestHandler:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }

    def fetch_sitemap(self, url):
        sitemap_url = urljoin(url, "/sitemap.xml")
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch sitemap: {e}")
            return None

    def fetch_page_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch page content: {e}")
            return None

    def get_favicon(self, url):
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        soup = BeautifulSoup(response.text, 'html.parser')
        icon_link = soup.find("link", rel="icon")
        favicon_url = urljoin(url, icon_link['href']) if icon_link else urljoin(url, "/favicon.ico")
        return favicon_url
    def parse_sitemap(self, ogurl, url, timeout=10, max_urls=10000, depth=0, processed_sitemaps=None, urls=None):
        """
        Fetch and parse a sitemap, handling nested sitemaps and limiting the number of URLs returned.

        Args:
            url (str): The base URL of the website (e.g., 'https://example.com').
            timeout (int, optional): Timeout for HTTP requests. Defaults to 10 seconds.
            max_urls (int, optional): Maximum number of URLs to return. Defaults to None (no limit).
            depth (int, optional): Current depth of sitemap parsing (used for nested sitemaps).
            processed_sitemaps (set, optional): Set of already processed sitemap URLs.
            urls (set, optional): Set of URLs collected so far.

        Returns:
            List[str]: A sorted list of URLs found in the sitemap(s), limited by max_urls if provided.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        def fetch_sitemap(sitemap_url):
            try:
                response = requests.get(sitemap_url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch {sitemap_url}: {e}")
                return None

        # Initialize processed_sitemaps and urls if not provided
        if processed_sitemaps is None:
            processed_sitemaps = set()
        if urls is None:
            urls = set()

        # Check if max_urls limit has been reached
        if max_urls and len(urls) >= max_urls:
            return sorted(urls, key=len)[:max_urls] if max_urls else sorted(urls, key=len)

        # Fetch and parse the sitemap
        sitemap_url = urljoin(url, "/sitemap.xml") if depth == 0 else url
        sitemap_content = fetch_sitemap(sitemap_url)

        if not sitemap_content:
            return urls

        soup = BeautifulSoup(sitemap_content, 'xml')
        print(f"Processing sitemap at depth {depth}")

        # Process nested sitemaps
        sitemaps = soup.find_all('sitemap')
        for sitemap in sitemaps:
            if max_urls and len(urls) >= max_urls:
                break  # Stop fetching more sitemaps if max_urls limit is reached

            nested_sitemap_url = sitemap.find('loc').text
            if nested_sitemap_url not in processed_sitemaps:
                print(f"Fetching nested sitemap: {nested_sitemap_url}")
                processed_sitemaps.add(nested_sitemap_url)
                nested_urls = self.parse_sitemap(ogurl, nested_sitemap_url, timeout, max_urls, depth + 1, processed_sitemaps, urls)
                urls.update(nested_urls)
                if max_urls and len(urls) >= max_urls:
                    return sorted(urls, key=len)[:max_urls] if max_urls else sorted(urls, key=len)

        # Process href links (URLs)
        url_tags = soup.find_all('loc')
        if not url_tags:
            url_tags = soup.find_all('url')  # Check for 'url' tag if 'loc' tag is not found

        # Skip sitemaps with more than 50 pages to avoid overwhelming the system
        if len(url_tags) > 1000:
            print(f"Skipping sitemap with {len(url_tags)} pages at depth {depth}")
            return urls

        for url_tag in url_tags:
            page_url = url_tag.text.strip()
            print(f"Found URL: {page_url}, strarts with url: {ogurl} {ogurl in page_url}")
            print(not page_url.endswith('.xml') and ogurl in page_url)
            if not page_url.endswith('.xml') and ogurl in page_url:  # Filter out XML URLs
                urls.add(page_url)
                print(f"Found URL: {page_url}")

            if max_urls and len(urls) >= max_urls:
                print(f"Max URLs limit reached: {max_urls}")
                return sorted(urls, key=len)[:max_urls] if max_urls else sorted(urls, key=len)

        # Return the list of URLs, limited by max_urls if provided and sorted by url length in ascending order
        return sorted(urls, key=len)[:max_urls] if max_urls else sorted(urls, key=len)