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
    submit_webhook = StringField()
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

class SalesScraperRuns(Document):
    meta = {'collection': 'sales_scraper_runs'}
    submission_id = ObjectIdField()
    email = StringField()
    url = StringField()
    description = StringField()
    run_type = StringField()
    run_status = StringField()
    run_start = me.DateTimeField()
    run_end = me.DateTimeField()
    run_duration = me.IntField()
    run_results = me.DictField()
    run_errors = me.DictField()
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()
    document_url = StringField()