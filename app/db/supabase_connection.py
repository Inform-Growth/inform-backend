import os
import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class SupabaseConnection:
    def __init__(self):
        url: str = os.environ.get('SUPABASE_URL')
        key: str = os.environ.get('SUPABASE_KEY')
        self.supabase: Client = create_client(url, key)

    def upload_file(self, file_path, bucket_name, file_name):
        """
        Upload a file to a specific bucket.
        """
        try:
            with open(file_path, 'rb') as file:
                response = self.supabase.storage.from_(bucket_name).upload(path=file_path, file=file, file_options={
                    'upsert': 'true',
                    'contentType': 'application/pdf'
                    })
            return response
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return None

    def create_submission(self, form_id, context, threads):
        """
        Create a new submission record and associated threads.
        """
        try:
            current_time = datetime.datetime.utcnow().isoformat()
            submission_data = {
                'form_id': form_id,
                'context': context,
                'tags': [],  # empty list
                'created_at': current_time,
                'updated_at': current_time,
                'version': 1  # or whatever initial value
            }
            response = self.supabase.table('submissions').insert(submission_data).execute()
            submission = response.data[0]
            submission_id = submission['id']
            # Now insert threads
            for thread in threads:
                thread_created_at = thread.get('created_at', current_time)
                # Ensure 'created_at' is a string
                if isinstance(thread_created_at, datetime.datetime):
                    thread_created_at = thread_created_at.isoformat()
                thread_data = {
                    'submission_id': submission_id,
                    'content': thread['content'],
                    'agent': thread['agent'],
                    'options_suggestions': thread.get('options_suggestions', []),
                    'created_at': thread_created_at
                }
                response_thread = self.supabase.table('threads').insert(thread_data).execute()
            return submission
        except Exception as e:
            print(f"Error creating submission: {str(e)}")
            return None

    def get_submissions(self, form_id):
        """
        Retrieve all submissions for a specific form ID.
        """
        try:
            response = self.supabase.table('submissions').select('*').eq('form_id', form_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching submissions: {str(e)}")
            return []

    def get_submission(self, submission_id):
        """
        Retrieve a specific submission by its ID.
        """
        try:
            response = self.supabase.table('submissions').select('*').eq('id', submission_id).single().execute()
            return response.data
        except Exception as e:
            print(f"Error fetching submission: {str(e)}")
            return None

    def search_submissions(self, query):
        """
        Search for submissions based on a query.
        """
        try:
            request = self.supabase.table('submissions').select('*')
            for key, value in query.items():
                request = request.eq(key, value)
            response = request.execute()
            return response.data
        except Exception as e:
            print(f"Error searching submissions: {str(e)}")
            return []

    def add_thread(self, submission_id, new_thread_item):
        """
        Add a new thread item to the threads table with the given submission_id.
        """
        try:
            current_time = datetime.datetime.utcnow().isoformat()
            thread_created_at = new_thread_item.get('created_at', current_time)
            # Ensure 'created_at' is a string
            if isinstance(thread_created_at, datetime.datetime):
                thread_created_at = thread_created_at.isoformat()
            thread_data = {
                'submission_id': submission_id,
                'content': new_thread_item['content'],
                'agent': new_thread_item['agent'],
                'options_suggestions': new_thread_item.get('options_suggestions', []),
                'created_at': thread_created_at
            }
            response = self.supabase.table('threads').insert(thread_data).execute()
            return True
        except Exception as e:
            print(f"Error adding thread item to submission: {str(e)}")
            return False

    def add_threads(self, submission_id, new_thread_items):
        """
        Add multiple new thread items to the threads table.
        """
        try:
            current_time = datetime.datetime.utcnow().isoformat()
            thread_data_list = []
            for item in new_thread_items:
                thread_created_at = item.get('created_at', current_time)
                # Ensure 'created_at' is a string
                if isinstance(thread_created_at, datetime.datetime):
                    thread_created_at = thread_created_at.isoformat()
                thread_data = {
                    'submission_id': submission_id,
                    'content': item['content'],
                    'agent': item['agent'],
                    'options_suggestions': item.get('options_suggestions', []),
                    'created_at': thread_created_at
                }
                thread_data_list.append(thread_data)
            response = self.supabase.table('threads').insert(thread_data_list).execute()
            return True
        except Exception as e:
            print(f"Error adding multiple thread items to submission: {str(e)}")
            return False

    def update_submission_tags(self, submission_id, new_tags):
        """
        Update the tags for a specific submission by adding new tags.
        """
        try:
            # First, fetch the current tags
            response = self.supabase.table('submissions').select('tags').eq('id', submission_id).single().execute()
            current_tags = response.data.get('tags', [])
            # Add new tags, avoiding duplicates
            updated_tags = list(set(current_tags + new_tags))
            # Update the submission's tags
            update_response = self.supabase.table('submissions').update({'tags': updated_tags}).eq('id', submission_id).execute()
            return True
        except Exception as e:
            print(f"Error updating submission tags: {str(e)}")
            return False

    def create_form(self, initial_fields, initial_fields_html, thank_you_html, form_type, form_purpose, examples, num_steps):
        """
        Create a new form record and associated initial fields.
        """
        try:
            current_time = datetime.datetime.utcnow().isoformat()
            form_data = {
                'initial_fields_html': initial_fields_html,
                'thank_you_html': thank_you_html,
                'form_type': form_type,
                'form_purpose': form_purpose,
                'examples': examples,
                'num_steps': num_steps,
                'created_at': current_time,
                'updated_at': current_time
            }
            response = self.supabase.table('forms').insert(form_data).execute()
            form = response.data[0]
            form_id = form['id']
            # Now insert initial_fields
            for field in initial_fields:
                field_data = {
                    'form_id': form_id,
                    'label': field['label'],
                    'type': field['type'],
                    'field_id': field['id'],  # Renamed to 'field_id' in SQL schema
                    'required': field['required']
                }
                response_field = self.supabase.table('initial_fields').insert(field_data).execute()
            return form
        except Exception as e:
            print(f"Error creating form: {str(e)}")
            return None

    def update_form(self, form_id, initial_fields=None, initial_fields_html=None, thank_you_html=None, form_type=None, form_purpose=None, examples=None, num_steps=None):
        """
        Update an existing form record and associated initial fields.
        """
        try:
            update_data = {}
            if initial_fields_html is not None:
                update_data['initial_fields_html'] = initial_fields_html
            if thank_you_html is not None:
                update_data['thank_you_html'] = thank_you_html
            if form_type is not None:
                update_data['form_type'] = form_type
            if form_purpose is not None:
                update_data['form_purpose'] = form_purpose
            if examples is not None:
                update_data['examples'] = examples
            if num_steps is not None:
                update_data['num_steps'] = num_steps
            if update_data:
                update_data['updated_at'] = datetime.datetime.utcnow().isoformat()
                response = self.supabase.table('forms').update(update_data).eq('id', form_id).execute()
            # Now handle initial_fields
            if initial_fields is not None:
                # Delete existing initial_fields for this form_id
                delete_response = self.supabase.table('initial_fields').delete().eq('form_id', form_id).execute()
                # Insert new initial_fields
                for field in initial_fields:
                    field_data = {
                        'form_id': form_id,
                        'label': field['label'],
                        'type': field['type'],
                        'field_id': field['id'],
                        'required': field['required']
                    }
                    response_field = self.supabase.table('initial_fields').insert(field_data).execute()
            # Return the updated form
            response_form = self.supabase.table('forms').select('*').eq('id', form_id).single().execute()
            return response_form.data
        except Exception as e:
            print(f"Error updating form: {str(e)}")
            return None

    def get_forms(self):
        """
        Retrieve all forms.
        """
        try:
            response = self.supabase.table('forms').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching forms: {str(e)}")
            return []

    def get_form(self, form_id):
        """
        Retrieve a specific form by its ID.
        """
        try:
            response = self.supabase.table('forms').select('*').eq('id', form_id).single().execute()
            return response.data
        except Exception as e:
            print(f"Error fetching form: {str(e)}")
            return None

    def search_number_runs_email(self, email):
        """
        Search for the number of runs for a specific email.
        """
        try:
            response = self.supabase.table('sales_scraper_runs').select('id', count='exact').eq('email', email).execute()
            return response.count
        except Exception as e:
            print(f"Error searching number of runs for email: {str(e)}")
            return 0

    def create_sales_scraper_run(self, email, description, url):
        """
        Create a new sales scraper run record.
        """
        try:
            current_time = datetime.datetime.utcnow().isoformat()
            run_data = {
                'email': email,
                'description': description,
                'url': url,
                'run_status': 'pending',
                'run_start': current_time,
                'run_results': {},
                'run_errors': {},
                'created_at': current_time,
                'updated_at': current_time
            }
            response = self.supabase.table('sales_scraper_runs').insert(run_data).execute()
            return response.data[0]
        except Exception as e:
            print(f"Error creating sales scraper run: {str(e)}")
            return None

    def update_sales_scraper_run(self, run_id, run_status, run_results="", run_errors=None):
        """
        Update an existing sales scraper run record.
        """
        try:
            current_time = datetime.datetime.utcnow().isoformat()
            update_data = {
                'run_status': run_status,
                'run_end': current_time,
                'run_results': run_results,
                'run_errors': run_errors if run_errors is not None else {},
                'updated_at': current_time
            }
            response = self.supabase.table('sales_scraper_runs').update(update_data).eq('id', run_id).execute()
            return response.data[0]
        except Exception as e:
            print(f"Error updating sales scraper run: {str(e)}")
            return None

    def store_documents(self, documents):
        """
        Store a list of documents in the database.
        """
        try:
            for doc in documents:
                doc_data = {
                    'metadata': doc.metadata,
                    'page_content': doc.page_content
                }
                response = self.supabase.table('web_documents').insert(doc_data).execute()
            return True
        except Exception as e:
            print(f"Error storing documents: {str(e)}")
            return False

    def get_documents(self):
        """
        Retrieve all documents.
        """
        try:
            response = self.supabase.table('web_documents').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching documents: {str(e)}")
            return []

    def search_documents(self, query):
        """
        Search for documents based on a query.
        """
        try:
            request = self.supabase.table('web_documents').select('*')
            for key, value in query.items():
                request = request.filter(f"{key}=eq.{value}")
            response = request.execute()
            return response.data
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    def search_documents_by_url(self, url):
        """
        Search for documents based on a URL.
        """
        try:
            response = self.supabase.table('web_documents').select('*').filter('metadata->>url', 'eq', url).execute()
            return response.data
        except Exception as e:
            print(f"Error searching documents by URL: {str(e)}")
            return []
