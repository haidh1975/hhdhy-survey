"""
Migration script to move data from JSON files to PostgreSQL database
"""
import json
import os
import logging
from datetime import datetime
from utils.database import init_database, SessionLocal
from utils.models import User, Survey, Response
from utils.db_utils import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_users():
    """Migrate users from users.json to database"""
    session = SessionLocal()
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            for username, user_info in users_data.items():
                # Check if user already exists
                existing_user = session.query(User).filter(User.username == username).first()
                if existing_user:
                    logger.info(f"User {username} already exists, skipping")
                    continue
                
                user = User(
                    username=username,
                    email=user_info.get('email', f"{username}@example.com"),
                    password_hash=user_info.get('password', hash_password('password123')),
                    role=user_info.get('role', 'user'),
                    active=user_info.get('active', True),
                    created_at=datetime.fromisoformat(user_info['created_at']) if user_info.get('created_at') else datetime.now(),
                    last_login=datetime.fromisoformat(user_info['last_login']) if user_info.get('last_login') else None
                )
                
                session.add(user)
                logger.info(f"Migrated user: {username}")
            
            session.commit()
            logger.info("Users migration completed")
        else:
            logger.info("No users.json file found")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error migrating users: {e}")
    finally:
        session.close()

def migrate_surveys():
    """Migrate surveys from surveys.json to database"""
    session = SessionLocal()
    try:
        if os.path.exists('surveys.json'):
            with open('surveys.json', 'r', encoding='utf-8') as f:
                surveys_data = json.load(f)
            
            # Get default admin user for survey ownership
            admin_user = session.query(User).filter(User.role == 'admin').first()
            if not admin_user:
                logger.error("No admin user found for survey ownership")
                return
            
            for survey_id, survey_info in surveys_data.items():
                # Check if survey already exists
                existing_survey = session.query(Survey).filter(Survey.uuid == survey_id).first()
                if existing_survey:
                    logger.info(f"Survey {survey_id} already exists, skipping")
                    continue
                
                survey = Survey(
                    uuid=survey_id,
                    title=survey_info.get('title', 'Untitled Survey'),
                    description=survey_info.get('description', ''),
                    questions=survey_info.get('questions', []),
                    created_by=admin_user.id,
                    created_at=datetime.fromisoformat(survey_info['created_date']) if survey_info.get('created_date') else datetime.now(),
                    active=True
                )
                
                session.add(survey)
                logger.info(f"Migrated survey: {survey_info.get('title', survey_id)}")
            
            session.commit()
            logger.info("Surveys migration completed")
        else:
            logger.info("No surveys.json file found")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error migrating surveys: {e}")
    finally:
        session.close()

def migrate_responses():
    """Migrate responses from responses.json to database"""
    session = SessionLocal()
    try:
        if os.path.exists('responses.json'):
            with open('responses.json', 'r', encoding='utf-8') as f:
                responses_data = json.load(f)
            
            for survey_uuid, responses_list in responses_data.items():
                # Get survey
                survey = session.query(Survey).filter(Survey.uuid == survey_uuid).first()
                if not survey:
                    logger.warning(f"Survey {survey_uuid} not found, skipping responses")
                    continue
                
                for response_data in responses_list:
                    response = Response(
                        survey_id=survey.id,
                        response_data=response_data,
                        submitted_at=datetime.fromisoformat(response_data['timestamp']) if response_data.get('timestamp') else datetime.now()
                    )
                    
                    session.add(response)
                
                logger.info(f"Migrated {len(responses_list)} responses for survey {survey_uuid}")
            
            session.commit()
            logger.info("Responses migration completed")
        else:
            logger.info("No responses.json file found")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error migrating responses: {e}")
    finally:
        session.close()

def run_migration():
    """Run complete migration process"""
    logger.info("Starting migration from JSON to PostgreSQL...")
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Run migrations in order
        migrate_users()
        migrate_surveys()
        migrate_responses()
        
        logger.info("Migration completed successfully!")
        
        # Backup JSON files
        backup_json_files()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def backup_json_files():
    """Backup original JSON files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    files_to_backup = ['users.json', 'surveys.json', 'responses.json', 'sessions.json']
    
    for filename in files_to_backup:
        if os.path.exists(filename):
            backup_name = f"{filename}.backup_{timestamp}"
            os.rename(filename, backup_name)
            logger.info(f"Backed up {filename} to {backup_name}")

if __name__ == "__main__":
    run_migration()