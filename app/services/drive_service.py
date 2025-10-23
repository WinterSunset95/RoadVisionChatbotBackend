from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from dateutil import parser
import io
import os
import re
import tempfile
import uuid

from app.config import settings
from app.core.services import upload_jobs
from app.services.document_processing_service import process_uploaded_pdf


# Google drive setup
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = None

def authenticate_google_drive():
    """Authenticates with the Google Drive API and returns a service object."""
    creds = None
    token_path = os.path.join(settings.ROOT_DIR, 'token.json')
    creds_path = os.path.join(settings.ROOT_DIR, 'credentials.json')
    
    # The file token.json stores the user's access and refresh tokens.
    # It's created automatically when the authorization flow completes for the first time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"❌ 'credentials.json' not found in root directory: {settings.ROOT_DIR}")
                return None
            # This will open a browser window for you to log in and authorize the app.
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    try:
        service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive API Authentication Successful!")
        return service
    except HttpError as error:
        print(f"An error occurred during authentication: {error}")
        return None

def download_files_from_drive(drive_url: str, conversation_id: str):
    """
    Downloads all files from a Google Drive folder and processes them.
    This function is intended to be run in a background task.
    """
    service = authenticate_google_drive()
    if not service:
        print("❌ Could not authenticate with Google Drive. Aborting download.")
        return

    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', drive_url)
    if not match:
        print(f"❌ Invalid Google Drive folder URL: {drive_url}")
        return
    folder_id = match.group(1)

    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name)"
        ).execute()
        items = results.get('files', [])

        if not items:
            print(f"No files found in the folder: {drive_url}")
            return

        for item in items:
            file_id = item['id']
            file_name = item['name']
            print(f"⬇️ Downloading {file_name} ({file_id})")

            request = service.files().get_media(fileId=file_id)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as tmp_file:
                downloader = MediaIoBaseDownload(tmp_file, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}%.")

                temp_path = tmp_file.name

            print(f"📂 File saved to temporary path: {temp_path}")
            
            # Now, process the downloaded file
            job_id = str(uuid.uuid4())
            upload_jobs[job_id] = {
                "filename": file_name,
                "status": "queued",
                "chat_id": conversation_id,
            }
            # Note: process_uploaded_pdf will handle cleanup of the temp file
            process_uploaded_pdf(temp_path, conversation_id, file_name, job_id)

    except HttpError as error:
        print(f'An error occurred: {error}')
