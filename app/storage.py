import json
from app.config import settings
from libcloud.storage.drivers.google_storage import GoogleStorageDriver
from google.oauth2 import service_account
from google.cloud import storage
from google.cloud.storage.bucket import Bucket

credentials = service_account.Credentials.from_service_account_file(settings.GOOGLE_CREDENTIALS)

storage_client = storage.Client(credentials=credentials)

bucket: Bucket = storage_client.bucket(settings.GOOGLE_STORAGE_BUCKET)

with open(settings.GOOGLE_CREDENTIALS) as f:
    credentials = json.load(f)

driver = GoogleStorageDriver(key=credentials['client_email'], secret=credentials['private_key'])

default_container = driver.get_container(settings.GOOGLE_STORAGE_BUCKET)

