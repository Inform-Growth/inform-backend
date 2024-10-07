import base64
import requests
import re
import os
from pyppeteer import launch
import asyncio

class DocumentHandler:
    def __init__(self):
        if not os.getenv('DISABLE_NEST_ASYNCIO', 'False').lower() in ['true', '1']:
            pass
            # nest_asyncio.apply()
        self.logo_link = "https://cdn.prod.website-files.com/66429a5efa070490dd2286c0/6645970b090e542c09ca3a25_informgrowth_logo_v1.png"
    
    async def generate_pdf(self, html_content, output_pdf_path, footer_html=None):
        print("Generating PDF...")
        browser = None
        try:
            # Launch a headless browser
            browser = await launch(headless=True, 
                               executablePath='/usr/bin/chromium',
                               args=[
                                '--no-sandbox',
                                '--disable-setuid-sandbox',
                                '--disable-dev-shm-usage',   # Helps reduce memory issues in Docker
                                '--disable-gpu',              # GPU rendering is not supported in headless mode in Docker
                                '--disable-software-rasterizer'
                            ])
            page = await browser.newPage()
            
            # Set the page content
            await page.setContent(html_content)
            
            # Wait until the content is fully loaded
            await asyncio.sleep(1)
            
            pdf_options = {
                'path': output_pdf_path,
                'format': 'A4',
                'printBackground': True,
                'margin': {
                    'top': '40px',
                    'bottom': '70px',  # Increased bottom margin to accommodate footer
                    'left': '40px',
                    'right': '40px'
                },
            }
            
            if footer_html:
                pdf_options.update({
                    'displayHeaderFooter': True,
                    'footerTemplate': footer_html,
                    'headerTemplate': '<span></span>',  # Empty header
                })
            
            # Generate PDF and save it to the specified output file
            await page.pdf(pdf_options)
            print(f"PDF generated at {output_pdf_path}")
            return output_pdf_path

        except Exception as e:
            print(f"Failed to generate PDF: {e}")
            raise e  # Re-raise the exception to handle it elsewhere if needed

        finally:
            if browser:
                await browser.close()
                print("Browser closed.")

    
    def get_favicon_html(self, favicon_url):
        favicon_html = ''
        if favicon_url:
            response = requests.get(favicon_url)
            if response.status_code == 200:
                img_data = base64.b64encode(response.content).decode('utf-8')
                favicon_html = f'<img src="data:image/png;base64,{img_data}" alt="Favicon" class="favicon">'
        return favicon_html

    def get_people_html(self, people):
        people_html = ''
        for person in people:
            people_html += f"""
                <div class="person">
                    <h3>{person.name}</h3>
                    <p><strong>Title:</strong> {person.title}</p>
                    <p><strong>Summary:</strong> {person.summary}</p>
                </div>
            """
        return people_html

    def get_appendix_html(self, appendix_urls):
        if not appendix_urls:
            return '<p>No appendices available.</p>'
        appendix_html = '<ul>'
        for url in appendix_urls:
            appendix_html += f'<li><a href="{url}">{url}</a></li>'
        appendix_html += '</ul>'
        return appendix_html

    async def generate_html_and_convert_to_pdf(self, company_summary, strategy, people, appendix_urls, pdf_filename, favicon_url, company_name, mission):
        try:
            # Build HTML content directly
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{company_name}</title>
                <style>
                    body {{
                        font-family: 'Helvetica Neue', Arial, sans-serif;
                        margin: 0 40px;  /* Adjusted margins */
                        line-height: 1.6;
                        color: #333;
                    }}
                    h1, h2, h3 {{
                        font-weight: bold;
                        margin-bottom: 20px;
                        color: #444;
                    }}
                    h1 {{
                        font-size: 36px;
                        border-bottom: 2px solid #ddd;
                        padding-bottom: 10px;
                        margin-top: 0;
                    }}
                    h2 {{
                        font-size: 28px;
                        border-bottom: 1px solid #eee;
                        padding-bottom: 8px;
                        margin-top: 40px;
                    }}
                    h3 {{
                        font-size: 22px;
                        margin-top: 30px;
                    }}
                    p {{
                        font-size: 16px;
                        margin-bottom: 20px;
                        text-align: justify;
                    }}
                    ul {{
                        margin-left: 20px;
                        margin-bottom: 20px;
                    }}
                    li {{
                        margin-bottom: 10px;
                    }}
                    .favicon {{
                        width: 50px;
                        height: 50px;
                    }}
                    .header {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 40px;
                        margin-top: 40px;
                    }}
                    .header h1 {{
                        margin-left: 20px;
                    }}
                    .person {{
                        margin-bottom: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    {self.get_favicon_html(favicon_url)}
                    <h1>{company_name}</h1>
                </div>
                <h2>Company Summary</h2>
                <p><strong>Summary:</strong> {company_summary.summary}</p>
                <p><strong>Mission:</strong> {mission}</p>
                {strategy}
                <h2>People Information</h2>
                {self.get_people_html(people)}
                <h2>Appendices</h2>
                {self.get_appendix_html(appendix_urls)}
            </body>
            </html>
            """

            # Get base64-encoded logo image for the footer
            logo_base64 = ''
            if self.logo_link:
                response = requests.get(self.logo_link)
                if response.status_code == 200:
                    logo_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Create footer HTML
            footer_html = f"""
            <div style="width:100%; text-align:center; font-size:12px;">
                <img src="data:image/png;base64,{logo_base64}" alt="Logo" style="width:100px; height:auto; margin-top:10px;">
            </div>
            """

            # Generate PDF from HTML
            file = await self.generate_pdf(html_content, pdf_filename, footer_html=footer_html)
            return file

        except Exception as e:
            print(f"Failed to generate HTML and convert to PDF: {e}")

    def clean_text(self, text):
        cleaned_text = re.sub(r'\n+', '\n', text)
        cleaned_text = cleaned_text.replace('\x00', '')
        cleaned_text = cleaned_text.strip()
        return cleaned_text
    
    def remove_duplicate_content(self, docs):
        for doc in docs:
            doc.page_content = self.clean_text(doc.page_content)
        
        def remove_common_prefix_suffix(texts):
            if not texts:
                return texts
            
            # Find common prefix
            prefix = os.path.commonprefix(texts)
            
            # Find common suffix
            reversed_texts = [text[::-1] for text in texts]
            reversed_suffix = os.path.commonprefix(reversed_texts)
            suffix = reversed_suffix[::-1]
            
            # Remove common prefix and suffix
            cleaned_texts = []
            for text in texts:
                start = len(prefix)
                end = len(text) - len(suffix) if suffix else len(text)
                cleaned = text[start:end]
                cleaned_texts.append(cleaned.strip())
            
            return cleaned_texts
    
        texts = [doc.page_content for doc in docs]
        cleaned_texts = remove_common_prefix_suffix(texts)
        
        for doc, cleaned_text in zip(docs, cleaned_texts):
            doc.page_content = cleaned_text
        
        return docs
