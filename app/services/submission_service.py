
# submission_service.py
from app.db.mongoengine_connection import MongoEngineConnection
from app.models.mongodb_models import Submission, Thread
from app.db.supabase_connection import SupabaseConnection
from app.services.form_chat_service import FormChatService
import datetime

class SubmissionService:
    def __init__(self):
        self.db = SupabaseConnection()
        self.inform_bot = FormChatService()

    def handle_initial_submission(self, form_id, context):
        # Generate the initial question first
        question = self.inform_bot.generate_question(form_id, context, [])
        initial_thread = Thread(
            content=question.question,
            agent="question",
            options_suggestions=question.suggestions,
            createdAt=datetime.datetime.now(datetime.UTC)
        )

        # Create a new submission document with the initial thread
        new_submission = self.db.create_submission(form_id, context, [initial_thread.to_mongo().to_dict()])
        if not new_submission:
            return "Error creating submission."
        
        return {"submission_id": str(new_submission.id), "question": question.question, "suggestions": question.suggestions}


    def handle_submission_response(self, submission_id, response):
        # Retrieve the submission
        submission = self.db.get_submission(submission_id)
        if not submission:
            return "Submission not found."

        # Prepare the response thread
        response_thread = Thread(
            content=response,
            agent="answer",
            createdAt=datetime.datetime.now(datetime.UTC)
        )

        # Generate the next question
        success_threads_dicts = [thread.to_mongo().to_dict() for thread in submission.thread]
        question = self.inform_bot.generate_question(str(submission.form_id.id), submission.context, success_threads_dicts)
        question_thread = Thread(
            content=question.question,
            agent="question",
            options_suggestions=question.suggestions,
            createdAt=datetime.datetime.now(datetime.UTC)
        )

        # Add both threads at once
        success = self.db.add_threads(submission_id, [response_thread.to_mongo().to_dict(), question_thread.to_mongo().to_dict()])
        if not success:
            return "Error adding thread items to submission."

        return {"submission_id": str(submission_id), "question": question.question, "suggestions": question.suggestions}
