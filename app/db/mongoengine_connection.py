import mongoengine as me
import os
import datetime
from app.models.mongodb_models import Submission, Thread, Form, SalesScraperRuns, WebDocument
from dotenv import load_dotenv
load_dotenv()


class MongoEngineConnection:
    def connect_to_mongo(self):
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        connection_string = (
            f"mongodb+srv://{db_user}:{db_pass}@cluster0.izevsxx.mongodb.net/inform?"
            "retryWrites=true&w=majority&appName=Cluster0"
        )
        me.disconnect()
        me.connect(host=connection_string, uuidRepresentation='standard')

    def __init__(self) -> None:
        self.connect_to_mongo()

    def create_submission(self, form_id, context, threads):
        """
        Create a new submission document.

        :param form_id: The ObjectId of the form related to the submission.
        :param context: A dictionary containing the context of the submission.
        :param tags: A list of tags associated with the submission.
        :return: Created Submission document or None if creation failed.
        """
        try:
            new_submission = Submission(
                form_id=form_id,
                context=context,
                tags=[],
                thread=threads,
                createdAt=datetime.datetime.now(datetime.UTC),
                updatedAt=datetime.datetime.now(datetime.UTC)
            )
            new_submission.save()
            return new_submission
        except Exception as e:
            print(f"Error creating submission: {str(e)}")
            return None

    def get_submissions(self, form_id):
        """
        Retrieve all submissions for a specific form ID.
        
        :param form_id: The ObjectId of the form to fetch submissions for.
        :return: List of Submission documents.
        """
        try:
            submissions = Submission.objects(form_id=form_id)
            return submissions
        except Exception as e:
            print(f"Error fetching submissions: {str(e)}")
            return []
        
    def get_submission(self, submission_id):
        """
        Retrieve a specific submission by its ID.
        
        :param submission_id: The ObjectId of the submission to fetch.
        :return: Submission document or None if not found.
        """
        try:
            submission = Submission.objects(id=submission_id).first()
            return submission
        except Exception as e:
            print(f"Error fetching submission: {str(e)}")
            return None
        
    def search_submissions(self, query):
        """
        Search for submissions based on a query.
        
        :param query: The search query.
        :return: List of Submission documents.
        """
        try:
            submissions = Submission.objects(__raw__=query)
            return submissions
        except Exception as e:
            print(f"Error searching submissions: {str(e)}")
            return []

    def add_thread(self, submission_id, new_thread_item):
        """
        Add a new thread item to the end of the thread list in a Submission document more efficiently.

        :param submission_id: The ObjectId of the submission to update.
        :param new_thread_item: The new thread item (a dictionary) to add.
        :return: Boolean indicating if the operation was successful.
        """
        try:
            # Ensure createdAt is set in new_thread_item
            if 'createdAt' not in new_thread_item:
                new_thread_item['createdAt'] = datetime.now(datetime.UTC)

            # Convert new_thread_item to a Thread document
            thread_document = Thread(**new_thread_item)

            # Update the submission directly in the database using update_one and push
            update_result = Submission.objects(id=submission_id).update_one(push__thread=thread_document)
            if update_result:
                return update_result
            else:
                print("Submission not found or no update performed.")
                return False
        except Exception as e:
            print(f"Error adding thread item to submission: {str(e)}")
            return False
        
    def add_threads(self, submission_id, new_thread_items):
        """
        Add multiple new thread items to the end of the thread list in a Submission document efficiently.

        :param submission_id: The ObjectId of the submission to update.
        :param new_thread_items: A list of new thread items (each a dictionary) to add.
        :return: Boolean indicating if the operation was successful.
        """
        from datetime import datetime

        try:
            # Ensure createdAt is set for each new thread item and convert them to Thread documents
            thread_documents = []
            for item in new_thread_items:
                if 'createdAt' not in item:
                    item['createdAt'] = datetime.now(datetime.UTC)
                thread_documents.append(Thread(**item))

            # Update the submission directly in the database using update_one and push_all
            update_result = Submission.objects(id=submission_id).update_one(push_all__thread=thread_documents)
            if update_result:
                return update_result
            else:
                print("Submission not found or no update performed.")
                return False
        except Exception as e:
            print(f"Error adding multiple thread items to submission: {str(e)}")
            return False

    def update_submission_tags(self, submission_id, new_tags):
        """
        Update the tags for a specific submission by adding new tags.
        
        :param submission_id: The ObjectId of the submission to update.
        :param new_tags: List of new tags to add.
        :return: Boolean indicating if the update was successful.
        """
        try:
            submission = Submission.objects(id=submission_id).first()
            if submission:
                submission.update(add_to_set__tags=new_tags)
                return True
            else:
                print("Submission not found.")
                return False
        except Exception as e:
            print(f"Error updating submission tags: {str(e)}")
            return False


    def create_form(self, initial_fields, initial_fields_html, thank_you_html, form_type, form_purpose, examples, num_steps):
        """
        Create a new form document.
        
        :param initial_fields: List of InitialField documents.
        :param initial_fields_html: HTML for the initial fields.
        :param thank_you_html: HTML for the thank you page.
        :param form_type: Type of the form.
        :param form_purpose: Purpose of the form.
        :param examples: List of example strings.
        :param num_steps: Number of steps in the form.
        :return: Created Form document or None if creation failed.
        """
        try:
            new_form = Form(
                initial_fields=initial_fields,
                initial_fields_html=initial_fields_html,
                thank_you_html=thank_you_html,
                form_type=form_type,
                form_purpose=form_purpose,
                examples=examples,
                num_steps=num_steps
            )
            new_form.save()
            return new_form
        except Exception as e:
            print(f"Error creating form: {str(e)}")
            return None

    def update_form(self, form_id, initial_fields=None, initial_fields_html=None, thank_you_html=None, form_type=None, form_purpose=None, examples=None, num_steps=None):
        """
        Update an existing form document.
        
        :param form_id: The ObjectId of the form to update.
        :param initial_fields: New list of InitialField documents (optional).
        :param initial_fields_html: New HTML for the initial fields (optional).
        :param thank_you_html: New HTML for the thank you page (optional).
        :param form_type: New type of the form (optional).
        :param form_purpose: New purpose of the form (optional).
        :param examples: New list of example strings (optional).
        :param num_steps: New number of steps in the form (optional).
        :return: Updated Form document or None if update failed.
        """
        try:
            form = Form.objects(id=form_id).first()
            if not form:
                print("Form not found.")
                return None
            
            if initial_fields is not None:
                form.initial_fields = initial_fields
            if initial_fields_html is not None:
                form.initial_fields_html = initial_fields_html
            if thank_you_html is not None:
                form.thank_you_html = thank_you_html
            if form_type is not None:
                form.form_type = form_type
            if form_purpose is not None:
                form.form_purpose = form_purpose
            if examples is not None:
                form.examples = examples
            if num_steps is not None:
                form.num_steps = num_steps
            
            form.updated_at = datetime.datetime.now(datetime.UTC)
            form.save()
            return form
        except Exception as e:
            print(f"Error updating form: {str(e)}")
            return None

    def get_forms(self):
        """
        Retrieve all forms.
        
        :return: List of Form documents.
        """
        try:
            forms = Form.objects()
            return forms
        except Exception as e:
            print(f"Error fetching forms: {str(e)}")
            return []
        
    def get_form(self, form_id):
        """
        Retrieve a specific form by its ID.
        
        :param form_id: The ObjectId of the form to fetch.
        :return: Form document or None if not found.
        """
        try:
            form = Form.objects(id=form_id).first()
            return form
        except Exception as e:
            print(f"Error fetching form: {str(e)}")
            return None
        
    def search_number_runs_email(self, email):
        """
        Search for the number of runs for a specific email.
        
        :param email: The email to search for.
        :return: Number of runs for the email.
        """
        try:
            count = SalesScraperRuns.objects(email=email).count()
            return count
        except Exception as e:
            print(f"Error searching number of runs for email: {str(e)}")
            return 0
    
    def create_sales_scraper_run(self, email, description, url):
        """
        Create a new sales scraper run document.
        
        :param email: The email associated with the run.
        :param description: The description of the run.
        :param run_type: The type of the run.
        :return: Created SalesScraperRuns document or None if creation failed.
        """
        try:
            new_run = SalesScraperRuns(
                email=email,
                description=description,
                url=url,
                run_status="pending",
                run_start=datetime.datetime.now(datetime.UTC),
                run_end=None,
                run_duration=None,
                run_results={},
                run_errors={},
                created_at=datetime.datetime.now(datetime.UTC),
                updated_at=datetime.datetime.now(datetime.UTC)
            )
            new_run.save()
            return new_run
        except Exception as e:
            print(f"Error creating sales scraper run: {str(e)}")
            return None
        
    def update_sales_scraper_run(self, run_id, run_status, run_results="", run_errors=None):
        """
        Update an existing sales scraper run document.
        
        :param run_id: The ObjectId of the run to update.
        :param run_status: The status of the run.
        :param run_end: The end time of the run.
        :param run_duration: The duration of the run.
        :param run_results: The results of the run.
        :param run_errors: The errors of the run.
        :return: Updated SalesScraperRuns document or None if update failed.
        """
        try:
            run = SalesScraperRuns.objects(id=run_id).first()
            if not run:
                print("Run not found.")
                return None
            
            run.run_status = run_status
            run.run_end = datetime.datetime.now(datetime.UTC)
            run.run_results = run_results
            run.run_errors = run_errors
            run.updated_at = datetime.datetime.now(datetime.UTC)
            run.save()
            return run
        except Exception as e:
            print(f"Error updating sales scraper run: {str(e)}")
            return None
        
    def store_documents(self, documents):
        """
        Store a list of documents in the database.
        
        :param documents: List of dictionaries representing documents.
        :return: Boolean indicating if the operation was successful.
        """
        try:
            for doc in documents:
                new_doc = WebDocument(**doc)
                WebDocument.save()
            return True
        except Exception as e:
            print(f"Error storing documents: {str(e)}")
            return False
        
    def get_documents(self):
        """
        Retrieve all documents.
        
        :return: List of WebDocument documents.
        """
        try:
            documents = WebDocument.objects()
            return documents
        except Exception as e:
            print(f"Error fetching documents: {str(e)}")
            return []
    def search_documents(self, query):
        """
        Search for documents based on a query.
        
        :param query: The search query.
        :return: List of WebDocument documents.
        """
        try:
            documents = WebDocument.objects(__raw__=query)
            return documents
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []
    def search_documents_by_url(self, url):
        """
        Search for documents based on a URL.
        
        :param url: The URL to search for.
        :return: List of WebDocument documents.
        """
        try:
            self.search_documents({"metadata": {"url": url}})
        except Exception as e:
            print(f"Error searching documents by URL: {str(e)}")
            return []