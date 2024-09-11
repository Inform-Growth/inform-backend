from app.core.config import CHAT_TEMPLATES
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from app.db.mongoengine_connection import MongoEngineConnection
from app.models.chat_models import QuestionModel
import os
class FormChatService:
    def __init__(self):

        print(os.getenv('GROQ_API_KEY'))
        
        self.db = MongoEngineConnection()
        self.forms = self.db.get_forms()
        self.form_map = {str(form.id): form for form in self.forms}
        self.form_context_ids = {str(form.id): [field.id for field in form.initial_fields] for form in self.forms}
        self.templates = CHAT_TEMPLATES
        self.chat_groq = ChatGroq(
                                    temperature=0,
                                    model="llama3-70b-8192",
                                    api_key=os.getenv('GROQ_API_KEY')
                                )
        
        
    def clean_submission(self, context, thread, form_id):
        # Extract context information
        cleaned_list = []
        form = self.form_map.get(form_id)
        # Convert context to the desired format
        for key, value in context.items():
            if key in self.form_context_ids[form_id]:
                question = [x for x in form.initial_fields if x.id == key][0]
                assert question
                cleaned_list.append({"question": question.label, "answer": value})
        
        # Extract thread information and consolidate content
        curr_qa = {}
        for entry in thread:
            content = entry.get('content', '')
            suggestions = entry.get('suggestions', [])
            if suggestions:
                curr_qa['question'] = content
            else:
                curr_qa['answer'] = content
                cleaned_list.append(curr_qa)
                curr_qa = {}

        return cleaned_list

    def format_for_prompt(self, cleaned_list):
        # Format the cleaned list into a string for the prompt
        formatted_list = []
        for item in cleaned_list:
            formatted_list.append(f"Question: {item['question']}\nAnswer: {item['answer']}")
    
        return "\n\n".join(formatted_list)

    def generate_question(self, form_id, initial_submission, thread):
        form = self.form_map.get(form_id)
        if not form:
            return "Form not found."
        
        form_type = form.form_type
        form_purpose = form.form_purpose

        # cleaned_list = self.clean_submission(initial_submission, thread, form_id)
        # questions = self.format_for_prompt(cleaned_list)
        previous_responses = []
        curr_qa = {}
        for entry in thread:
            content = entry.get('content', '')
            suggestions = entry.get('suggestions', [])
            if suggestions:
                curr_qa['question'] = content
            else:
                curr_qa['answer'] = content
                previous_responses.append(curr_qa)
                curr_qa = {}

        # previous_responses = "\n".join([f"{k}: {v}" for k, v in thread.items()])
        
        template = self.templates.get(form_type)
        if not template:
            return "Template not found."
        
        chain = ChatPromptTemplate.from_messages(self.templates[form_type]) | self.chat_groq.with_structured_output(QuestionModel)
        print(previous_responses)
        return chain.invoke({
            "form_purpose":form_purpose,
            "initial_submission":initial_submission,
            "previous_responses":previous_responses,
            "questions":form.examples,
        }
        )