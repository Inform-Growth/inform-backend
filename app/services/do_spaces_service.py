import boto3
from botocore.client import Config
import botocore
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
load_dotenv()

class DigitalOceanSpacesUploader:
    def __init__(self, space_name, region=None, endpoint_url=None):
        # Load environment variables

        # Retrieve keys from the environment
        self.space_name = space_name
        self.access_key_id = os.getenv('DO_SPACES_KEY')
        self.secret_access_key = os.getenv('DO_SPACES_SECRET')
        self.region = region or os.getenv('DO_SPACES_REGION')
        self.endpoint_url = endpoint_url or os.getenv('DO_SPACES_ENDPOINT')
        print(f"Space name: {self.space_name}, Access key: {self.access_key_id}, Secret key: {self.secret_access_key}, Region: {self.region}, Endpoint: {self.endpoint_url}")

        # Initialize the boto3 session
        print("Creating client")
        self.session = boto3.session.Session()
        self.client = self.session.client('s3',
                        endpoint_url='https://sfo2.digitaloceanspaces.com', # Find your endpoint in the control panel, under Settings. Prepend "https://".
                        config=botocore.config.Config(s3={'addressing_style': 'virtual'}), # Configures to use subdomain/virtual calling format.
                        region_name='sfo2', # Use the region in your endpoint.
                        aws_access_key_id='DO00BJHJEAJL9LJ6V9H4', # Access key pair. You can create access key pairs using the control panel or API.
                        aws_secret_access_key=os.getenv('DO_SPACES_KEY'))
        print(self.client)

    def bucket_exists(self, bucket_name):
        try:
            self.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def upload_file(self, file_name):
        try:
            if not self.bucket_exists(self.space_name):
                self.client.create_bucket(Bucket=self.space_name)
                print(f"Bucket '{self.space_name}' created.")
            else:
                print(f"Bucket '{self.space_name}' already exists.")

            # Upload file
            with open(file_name, 'rb') as file_data:
                self.client.put_object(Bucket=self.space_name, Key=file_name, Body=file_data, Metadata={'Content-Type': 'application/pdf', 'ACL': "public-read"})
                print(f"File '{file_name}' uploaded to bucket '{self.space_name}'.")
            self.client.put_object_acl(Bucket=self.space_name, Key=file_name, ACL='public-read')

        except ClientError as e:
            print(f"Client error: {e}")
