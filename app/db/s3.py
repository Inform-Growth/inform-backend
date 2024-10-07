import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()

class S3Connection:
    def __init__(self):
        # Load AWS credentials from environment variables
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.region_name = os.environ.get('AWS_REGION', 'us-east-1')  # Default to us-east-1 if not specified
        
        # Initialize the S3 client
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=self.aws_access_key_id,
                                      aws_secret_access_key=self.aws_secret_access_key,
                                      region_name=self.region_name)
        
        self.bucket_name = 'inform-scraper'

    def upload_file(self, file_path, object_name=None):
        """
        Upload a file to S3 bucket
        
        :param file_path: File to upload
        :param object_name: S3 object name. If not specified, file_name is used
        :return: True if file was uploaded, else False
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
        except ClientError as e:
            print(f"Error uploading file: {str(e)}")
            return False
        return True

    def list_files(self):
        """
        List files in the S3 bucket
        
        :return: List of file names in the bucket
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            print(f"Error listing files: {str(e)}")
            return []

    def download_file(self, object_name, file_path):
        """
        Download a file from S3 bucket
        
        :param object_name: S3 object name to download
        :param file_path: Local path to save the downloaded file
        :return: True if file was downloaded, else False
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
        except ClientError as e:
            print(f"Error downloading file: {str(e)}")
            return False
        return True