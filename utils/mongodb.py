# Import necessary libraries
import mongoengine as me
from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, EmbeddedDocument, EmbeddedDocumentListField, ObjectIdField
import os
import datetime


# Define document models
class InitialField(EmbeddedDocument):
    label = StringField()
    type = StringField()
    id = StringField()
    required = BooleanField()

class Form(Document):
    meta = {'collection': 'forms'}
    initial_fields = EmbeddedDocumentListField(InitialField)
    initial_fields_html = StringField()
    name = StringField()
    thank_you_html = StringField()
    form_type = StringField(choices=['lead_gen', 'survey', 'ticketing', 'review'])
    form_purpose = StringField()
    examples = ListField(StringField())
    num_steps = me.IntField()
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()

class Thread(EmbeddedDocument):
    content = StringField(required=True)
    agent = StringField(choices=['question', 'answer'], required=True)
    options_suggestions = ListField(StringField())
    createdAt = me.DateTimeField(default=datetime.datetime.now(datetime.UTC))

# Update the Submission document to include a ListField of Thread type
class Submission(Document):
    meta = {'collection': 'submissions',
            'strict': False}
    form_id = ReferenceField(Form, required=True)
    context = me.DictField()
    thread = EmbeddedDocumentListField(Thread)
    tags = ListField(StringField())
    createdAt = me.DateTimeField()
    updatedAt = me.DateTimeField()
    __v = me.IntField()
class MongoEngineConnection:
    def connect_to_mongo(self):
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        connection_string = (
            f"mongodb+srv://{db_user}:{db_pass}@cluster0.izevsxx.mongodb.net/inform?"
            "retryWrites=true&w=majority&appName=Cluster0"
        )
        me.disconnect()
        me.connect(host=connection_string)

        # Call the connection function
    def __init__(self) -> None:
        self.connect_to_mongo()

    def create_submission(self, form_id, context):
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

    def add_thread(self, submission_id, new_thread_item):
        """
        Add a new thread item to the end of the thread list in a Submission document.

        :param submission_id: The ObjectId of the submission to update.
        :param new_thread_item: The new thread item (a dictionary) to add.
        :return: Boolean indicating if the operation was successful.
        """
        try:
            submission = Submission.objects(id=submission_id).first()
            if submission:
                # Ensure createdAt is set in new_thread_item
                if 'createdAt' not in new_thread_item:
                    new_thread_item['createdAt'] = datetime.datetime.now(datetime.UTC)
                
                # Convert new_thread_item to a Thread document
                thread_document = Thread(**new_thread_item)
                
                # Add the new Thread document to the submission's thread list
                submission.update(push__thread=thread_document)
                return submission
            else:
                print("Submission not found.")
                return False
        except Exception as e:
            print(f"Error adding thread item to submission: {str(e)}")
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


# mongodb = MongoEngineConnection()