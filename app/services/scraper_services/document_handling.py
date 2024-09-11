import markdown
import base64
import requests
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage

class DocumentHandler:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles['Title'].fontSize = 24
        self.styles['Title'].spaceAfter = 12
        self.styles['Heading1'].fontSize = 18
        self.styles['Heading1'].spaceAfter = 6
        self.styles['Heading2'].fontSize = 16
        self.styles['Heading2'].spaceAfter = 6
        self.styles['Heading3'].fontSize = 14
        self.styles['Heading3'].spaceAfter = 6
        self.styles['BodyText'].fontSize = 12
        self.styles['BodyText'].spaceAfter = 6

    def save_to_markdown_and_convert_to_pdf(self, company_summary, strategy, people, appendix_urls, pdf_filename, favicon_url, company_name, mission):
        try:
            markdown_content = f"# Company Summary\n\n"
            markdown_content += f"**Summary:** {company_summary}\n\n"
            markdown_content += f"**Mission:** {mission}\n\n"
            markdown_content += f"# Strategy and Approach\n\n"
            markdown_content += f"{strategy}\n\n"
            markdown_content += f"# People Information\n\n"
            for person in people:
                if 'name' not in person or 'title' not in person or 'summary' not in person:
                    continue
                markdown_content += f"### {person['name']}\n\n"
                markdown_content += f"**Title:** {person['title']}\n\n"
                markdown_content += f"**Summary:** {person['summary']}\n\n"
            markdown_content += f"# Appendices\n\n"
            for url in appendix_urls:
                markdown_content += f"* [{url}]({url})\n\n"

            html_content = markdown.markdown(markdown_content)

            # Create a PDF document
            doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
            story = []

            # Add favicon and company name
            header = []
            response = requests.get(favicon_url)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                img = PILImage.open(img_data)
                img = img.convert('RGB')
                img_io = BytesIO()
                img.save(img_io, format='PNG')
                img_data = img_io.getvalue()
                favicon = Image(BytesIO(img_data), width=32, height=32)
                header.append(favicon)
            header.append(Paragraph(company_name, self.styles['Title']))
            story.append(Paragraph(" ".join([str(item) for item in header]), self.styles['BodyText']))
            story.append(Spacer(1, 0.25*inch))

            # Convert HTML to ReportLab elements
            for element in html_content.split('\n'):
                if element.startswith('<h1>'):
                    story.append(Paragraph(element[4:-5], self.styles['Heading1']))
                elif element.startswith('<h2>'):
                    story.append(Paragraph(element[4:-5], self.styles['Heading2']))
                elif element.startswith('<h3>'):
                    story.append(Paragraph(element[4:-5], self.styles['Heading3']))
                elif element.startswith('<p>'):
                    story.append(Paragraph(element[3:-4], self.styles['BodyText']))
                elif element.startswith('<ul>'):
                    continue
                elif element.startswith('<li>'):
                    story.append(Paragraph('• ' + element[4:-5], self.styles['BodyText']))
                else:
                    story.append(Paragraph(element, self.styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))

            doc.build(story)

        except Exception as e:
            print(f"Failed to save markdown and convert to PDF: {str(e)}")
            raise

    def clean_text(self, text):
        cleaned_text = re.sub(r'\n+', '\n', text)
        cleaned_text = cleaned_text.strip()
        return cleaned_text

    def remove_duplicate_content(self, docs):
        for doc in docs:
            doc.page_content = self.clean_text(doc.page_content)
        
        def remove_common_prefix_suffix(texts):
            if not texts:
                return texts
            
            prefix = texts[0]
            for s in texts[1:]:
                prefix = prefix[:len(s)] if len(s) < len(prefix) else prefix
                prefix = ''.join(c1 for c1, c2 in zip(prefix, s) if c1 == c2)
                if not prefix:
                    break
            
            suffix = texts[0][::-1]
            for s in texts[1:]:
                s = s[::-1]
                suffix = suffix[:len(s)] if len(s) < len(suffix) else suffix
                suffix = ''.join(c1 for c1, c2 in zip(suffix, s) if c1 == c2)
                if not suffix:
                    break
            suffix = suffix[::-1]
            
            cleaned_texts = []
            for text in texts:
                cleaned = text[len(prefix):] if text.startswith(prefix) else text
                cleaned = cleaned[:-len(suffix)] if cleaned.endswith(suffix) else cleaned
                cleaned_texts.append(cleaned.strip())
            
            return cleaned_texts

        texts = [doc.page_content for doc in docs]
        cleaned_texts = remove_common_prefix_suffix(texts)
        
        for doc, cleaned_text in zip(docs, cleaned_texts):
            doc.page_content = cleaned_text
        
        return docs