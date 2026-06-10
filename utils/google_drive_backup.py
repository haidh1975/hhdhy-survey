"""
Google Drive Backup Integration for Survey Application
"""
import os
import io
import json
import pickle
import logging
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd

try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Scopes needed for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveManager:
    """Manages Google Drive operations for survey data backup"""
    
    def __init__(self, credentials_file: str = 'google_credentials.json', token_file: str = 'google_token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.survey_folder_id = None
        self.use_service_account = False
        
        # Check for service account credentials in environment
        if os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'):
            self.use_service_account = True
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API using service account or OAuth
        Returns True if successful, False otherwise
        """
        try:
            creds = None
            
            if self.use_service_account:
                # Use service account authentication (production)
                creds = self._authenticate_service_account()
            else:
                # Use OAuth flow (development)
                creds = self._authenticate_oauth()
            
            if not creds:
                logger.error("Failed to obtain credentials")
                return False
            
            # Build the Drive service
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            return False
    
    def _authenticate_service_account(self) -> Optional[Any]:
        """
        Authenticate using service account credentials from environment variables
        """
        try:
            # Get service account key from environment
            service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
            if not service_account_key:
                logger.error("GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set")
                return None
            
            # Decode base64 encoded key if needed
            try:
                service_account_info = json.loads(base64.b64decode(service_account_key).decode('utf-8'))
            except:
                # If not base64 encoded, try direct JSON
                service_account_info = json.loads(service_account_key)
            
            # Create credentials from service account info
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES)
            
            logger.info("Service account authentication successful")
            return creds
            
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            return None
    
    def _authenticate_oauth(self) -> Optional[Any]:
        """
        Authenticate using OAuth flow for development
        """
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Refreshed existing credentials")
                    except Exception as e:
                        logger.warning(f"Failed to refresh credentials: {e}")
                        creds = None
                
                if not creds:
                    # Try environment variable first
                    oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
                    if oauth_credentials:
                        try:
                            # Decode base64 if needed
                            try:
                                credentials_data = json.loads(base64.b64decode(oauth_credentials).decode('utf-8'))
                            except:
                                credentials_data = json.loads(oauth_credentials)
                            
                            # Create temporary file for OAuth flow
                            temp_creds_file = '/tmp/temp_oauth_creds.json'
                            with open(temp_creds_file, 'w') as f:
                                json.dump(credentials_data, f)
                            
                            flow = InstalledAppFlow.from_client_secrets_file(
                                temp_creds_file, SCOPES)
                            
                            # Clean up temp file
                            os.remove(temp_creds_file)
                        except Exception as env_error:
                            logger.warning(f"Failed to use OAuth credentials from environment: {env_error}")
                            return None
                    elif os.path.exists(self.credentials_file):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, SCOPES)
                    else:
                        logger.error("No OAuth credentials found in environment or file")
                        return None
                    
                    # Use console flow for headless environments
                    try:
                        creds = flow.run_console()
                        logger.info("Console authentication completed")
                    except Exception as console_error:
                        logger.error(f"Console authentication failed: {console_error}")
                        # Fallback to local server for development
                        try:
                            creds = flow.run_local_server(port=0)
                            logger.info("Local server authentication completed")
                        except Exception as local_error:
                            logger.error(f"Local server authentication failed: {local_error}")
                            return None
                
                # Save credentials for future use (only for OAuth)
                if creds and not self.use_service_account:
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)
            
            return creds
            
        except Exception as e:
            logger.error(f"OAuth authentication failed: {e}")
            return None
    
    def _ensure_survey_folder(self) -> Optional[str]:
        """
        Ensure survey backup folder exists, create if not
        Returns folder ID
        """
        if not self.service:
            return None
            
        try:
            folder_name = "Survey_Backup_HungYen"
            
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                self.survey_folder_id = folders[0]['id']
                logger.info(f"Found existing backup folder: {self.survey_folder_id}")
            else:
                # Create new folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                self.survey_folder_id = folder.get('id')
                logger.info(f"Created new backup folder: {self.survey_folder_id}")
            
            return self.survey_folder_id
            
        except Exception as e:
            logger.error(f"Error ensuring survey folder: {e}")
            return None
    
    def upload_file(self, file_path: str, file_name: Optional[str] = None, description: str = "") -> Optional[str]:
        """
        Upload file to Google Drive backup folder
        Returns file ID if successful
        """
        if not self.service:
            logger.error("Google Drive service not authenticated")
            return None
        
        try:
            folder_id = self._ensure_survey_folder()
            if not folder_id:
                return None
            
            if not file_name:
                file_name = os.path.basename(file_path)
            
            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = file_name.rsplit('.', 1)
            if len(name_parts) == 2:
                file_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                file_name = f"{file_name}_{timestamp}"
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id],
                'description': description
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size'
            ).execute()
            
            file_id = file.get('id')
            file_size = file.get('size', 0)
            logger.info(f"Uploaded {file_name} to Google Drive. ID: {file_id}, Size: {file_size} bytes")
            
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading file to Google Drive: {e}")
            return None
    
    def upload_data_as_json(self, data: Dict[str, Any], filename: str, description: str = "") -> Optional[str]:
        """
        Upload Python data as JSON file to Google Drive
        """
        try:
            # Create temporary JSON file
            temp_file = f"/tmp/{filename}"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Upload to Google Drive
            file_id = self.upload_file(temp_file, filename, description)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading data as JSON: {e}")
            return None
    
    def upload_dataframe_as_excel(self, df: pd.DataFrame, filename: str, description: str = "") -> Optional[str]:
        """
        Upload DataFrame as Excel file to Google Drive
        """
        try:
            # Create temporary Excel file
            temp_file = f"/tmp/{filename}"
            df.to_excel(temp_file, index=False, engine='openpyxl')
            
            # Upload to Google Drive
            file_id = self.upload_file(temp_file, filename, description)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading DataFrame as Excel: {e}")
            return None
    
    def list_backup_files(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List backup files in Google Drive folder
        """
        if not self.service:
            return []
        
        try:
            folder_id = self._ensure_survey_folder()
            if not folder_id:
                return []
            
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                pageSize=limit,
                fields="files(id, name, size, createdTime, modifiedTime, description)",
                orderBy="createdTime desc"
            ).execute()
            
            files = results.get('files', [])
            return files
            
        except Exception as e:
            logger.error(f"Error listing backup files: {e}")
            return []
    
    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download file from Google Drive
        """
        if not self.service:
            return False
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Save to local file
            with open(destination_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Downloaded file {file_id} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    def get_file_mime_type(self, file_name: str) -> str:
        """
        Get MIME type based on file extension
        """
        extension = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        mime_types = {
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'csv': 'text/csv',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'zip': 'application/zip'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from Google Drive
        """
        if not self.service:
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file {file_id} from Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

# Survey backup functions
def backup_surveys_to_drive(drive_manager: GoogleDriveManager) -> Optional[str]:
    """
    Backup all surveys to Google Drive
    """
    try:
        from utils.db_utils import get_surveys_db
        
        surveys = get_surveys_db()
        if not surveys:
            logger.info("No surveys to backup")
            return None
        
        backup_data = {
            "backup_date": datetime.now().isoformat(),
            "surveys_count": len(surveys),
            "surveys": surveys
        }
        
        filename = "surveys_backup.json"
        description = f"Survey backup - {len(surveys)} surveys - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        file_id = drive_manager.upload_data_as_json(backup_data, filename, description)
        return file_id
        
    except Exception as e:
        logger.error(f"Error backing up surveys: {e}")
        return None

def backup_responses_to_drive(drive_manager: GoogleDriveManager, survey_uuid: Optional[str] = None) -> Optional[str]:
    """
    Backup survey responses to Google Drive
    """
    try:
        from utils.db_utils import get_responses_db, get_surveys_db
        
        if survey_uuid:
            # Backup specific survey responses
            responses = get_responses_db(survey_uuid)
            survey_data = get_surveys_db()
            survey_info = next((s for s in survey_data if s['uuid'] == survey_uuid), None)
            
            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "survey_uuid": survey_uuid,
                "survey_title": survey_info['title'] if survey_info else "Unknown",
                "responses_count": len(responses),
                "responses": responses
            }
            
            filename = f"responses_{survey_uuid[:8]}_backup.json"
            description = f"Responses backup for survey {survey_uuid[:8]} - {len(responses)} responses"
        else:
            # Backup all responses
            surveys = get_surveys_db()
            all_responses = {}
            total_responses = 0
            
            for survey in surveys:
                responses = get_responses_db(survey['uuid'])
                all_responses[survey['uuid']] = {
                    'survey_title': survey['title'],
                    'responses': responses
                }
                total_responses += len(responses)
            
            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "total_responses": total_responses,
                "surveys_with_responses": all_responses
            }
            
            filename = "all_responses_backup.json"
            description = f"All responses backup - {total_responses} total responses"
        
        file_id = drive_manager.upload_data_as_json(backup_data, filename, description)
        return file_id
        
    except Exception as e:
        logger.error(f"Error backing up responses: {e}")
        return None

def backup_users_to_drive(drive_manager: GoogleDriveManager) -> Optional[str]:
    """
    Backup user data to Google Drive (excluding sensitive information)
    """
    try:
        from utils.db_utils import get_all_users_db
        
        users = get_all_users_db()
        if not users:
            logger.info("No users to backup")
            return None
        
        # Remove sensitive data before backup
        safe_users = []
        for user in users:
            safe_user = {
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role"),
                "active": user.get("active"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
                # Note: password_hash is excluded for security
            }
            safe_users.append(safe_user)
        
        backup_data = {
            "backup_date": datetime.now().isoformat(),
            "users_count": len(safe_users),
            "users": safe_users
        }
        
        filename = "users_backup.json"
        description = f"Users backup - {len(safe_users)} users - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        file_id = drive_manager.upload_data_as_json(backup_data, filename, description)
        return file_id
        
    except Exception as e:
        logger.error(f"Error backing up users: {e}")
        return None

def create_full_backup(drive_manager: GoogleDriveManager) -> Dict[str, Optional[str]]:
    """
    Create a complete backup of the survey system
    """
    backup_results = {}
    
    # Backup surveys
    backup_results['surveys'] = backup_surveys_to_drive(drive_manager)
    
    # Backup all responses
    backup_results['responses'] = backup_responses_to_drive(drive_manager)
    
    # Backup users
    backup_results['users'] = backup_users_to_drive(drive_manager)
    
    # Create summary
    successful_backups = sum(1 for result in backup_results.values() if result is not None)
    logger.info(f"Backup completed: {successful_backups}/3 components backed up successfully")
    
    return backup_results

def get_google_drive_config_status() -> Dict[str, Any]:
    """
    Get detailed configuration status for Google Drive
    """
    status = {
        "configured": False,
        "method": None,
        "service_account": False,
        "oauth_env": False,
        "oauth_file": False,
        "recommendations": []
    }
    
    # Check service account
    if os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'):
        status["configured"] = True
        status["method"] = "service_account"
        status["service_account"] = True
        status["recommendations"].append("✅ Service Account được cấu hình - Phương pháp bảo mật nhất")
    
    # Check OAuth from environment
    elif os.getenv('GOOGLE_OAUTH_CREDENTIALS'):
        status["configured"] = True
        status["method"] = "oauth_env"
        status["oauth_env"] = True
        status["recommendations"].append("✅ OAuth từ environment variable - Tốt cho development")
        status["recommendations"].append("💡 Nên chuyển sang Service Account cho production")
    
    # Check OAuth from file (legacy)
    elif os.path.exists('google_credentials.json'):
        status["configured"] = True
        status["method"] = "oauth_file"
        status["oauth_file"] = True
        status["recommendations"].append("⚠️ OAuth từ file - Không an toàn cho production")
        status["recommendations"].append("🔧 Nên chuyển sang environment variable")
    
    else:
        status["recommendations"].append("❌ Chưa cấu hình Google Drive")
        status["recommendations"].append("📋 Làm theo hướng dẫn để thiết lập")
    
    return status

# Utility function to check if Google Drive is configured
def is_google_drive_configured() -> bool:
    """
    Check if Google Drive credentials are configured
    """
    # Check for service account credentials in environment
    if os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'):
        return True
    
    # Check for OAuth credentials in environment
    if os.getenv('GOOGLE_OAUTH_CREDENTIALS'):
        return True
    
    # Fallback to check for legacy file-based credentials (development only)
    return os.path.exists('google_credentials.json')

def setup_google_drive_instructions() -> str:
    """
    Return setup instructions for Google Drive integration
    """
    return """
    ## Cách thiết lập Google Drive Backup an toàn:
    
    ### Phương pháp 1: Service Account (Khuyến nghị cho Production)
    
    1. **Tạo Google Cloud Project:**
       - Truy cập https://console.cloud.google.com/
       - Tạo project mới hoặc chọn project hiện có
    
    2. **Kích hoạt Google Drive API:**
       - Vào APIs & Services > Library
       - Tìm và kích hoạt "Google Drive API"
    
    3. **Tạo Service Account:**
       - Vào APIs & Services > Credentials
       - Click "Create Credentials" > "Service Account"
       - Đặt tên và mô tả cho service account
       - Tạo và tải về JSON key file
    
    4. **Cấu hình Environment Variable:**
       - Encode JSON key bằng base64: `base64 -i service-account-key.json`
       - Thêm environment variable: `GOOGLE_SERVICE_ACCOUNT_KEY=<base64_encoded_key>`
    
    ### Phương pháp 2: OAuth (Cho Development)
    
    1. **Tạo OAuth 2.0 Credentials:**
       - Vào APIs & Services > Credentials
       - Click "Create Credentials" > "OAuth 2.0 Client ID"
       - Chọn "Desktop application"
       - Tải file credentials.json
    
    2. **Cấu hình Environment Variable:**
       - Encode JSON bằng base64: `base64 -i credentials.json`
       - Thêm environment variable: `GOOGLE_OAUTH_CREDENTIALS=<base64_encoded_credentials>`
    
    ### Lưu ý bảo mật:
    - **KHÔNG BAO GIỜ** commit credentials vào code repository
    - Sử dụng environment variables hoặc secrets management
    - Service Account an toàn hơn cho môi trường production
    - OAuth phù hợp cho development và testing
    """