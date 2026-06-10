import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from utils.database import SessionLocal
from utils.models import User, Survey, Response

logger = logging.getLogger(__name__)

# User Management Functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_db(username: str, email: str, password: str, role: str = "user") -> tuple[bool, str]:
    """Create a new user in database"""
    session = SessionLocal()
    try:
        # Check if username exists
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            return False, "Tên đăng nhập đã tồn tại"
        
        # Check if email exists
        existing_email = session.query(User).filter(User.email == email).first()
        if existing_email:
            return False, "Email đã được sử dụng"
        
        # Validation
        if len(username) < 3:
            return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
        if len(password) < 6:
            return False, "Mật khẩu phải có ít nhất 6 ký tự"
        if "@" not in email:
            return False, "Email không hợp lệ"
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            active=True
        )
        
        session.add(new_user)
        session.commit()
        logger.info(f"Created user: {username}")
        return True, "Tài khoản được tạo thành công"
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating user: {e}")
        return False, f"Lỗi tạo tài khoản: {str(e)}"
    finally:
        session.close()

def authenticate_user_db(username: str, password: str) -> tuple[bool, Optional[Dict], str]:
    """Authenticate user with database"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        
        if not user:
            return False, None, "Tên đăng nhập không tồn tại"
        
        if not user.active:
            return False, None, "Tài khoản đã bị vô hiệu hóa"
        
        if user.password_hash != hash_password(password):
            return False, None, "Mật khẩu không chính xác"
        
        # Update last login
        user.last_login = datetime.now()
        session.commit()
        
        return True, user.to_dict(), "Đăng nhập thành công"
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return False, None, f"Lỗi đăng nhập: {str(e)}"
    finally:
        session.close()

def get_all_users_db() -> List[Dict]:
    """Get all users from database"""
    session = SessionLocal()
    try:
        users = session.query(User).all()
        return [user.to_dict() for user in users]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []
    finally:
        session.close()

def update_user_status_db(username: str, active: bool) -> tuple[bool, str]:
    """Update user active status"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False, "Người dùng không tồn tại"
        
        user.active = active
        session.commit()
        
        status_text = "kích hoạt" if active else "vô hiệu hóa"
        return True, f"Đã {status_text} tài khoản {username}"
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating user status: {e}")
        return False, f"Lỗi cập nhật: {str(e)}"
    finally:
        session.close()

def change_user_role_db(username: str, new_role: str) -> tuple[bool, str]:
    """Change user role"""
    session = SessionLocal()
    try:
        if new_role not in ["admin", "user"]:
            return False, "Vai trò không hợp lệ"
        
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False, "Người dùng không tồn tại"
        
        user.role = new_role
        session.commit()
        
        return True, f"Đã thay đổi vai trò của {username} thành {new_role}"
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error changing user role: {e}")
        return False, f"Lỗi thay đổi vai trò: {str(e)}"
    finally:
        session.close()

# Survey Management Functions
def create_survey_db(title: str, description: str, questions: List[Dict], created_by: int) -> tuple[bool, str, Optional[str]]:
    """Create a new survey in database"""
    session = SessionLocal()
    try:
        survey = Survey(
            title=title,
            description=description,
            questions=questions,
            created_by=created_by,
            active=True
        )
        
        session.add(survey)
        session.commit()
        session.refresh(survey)
        
        logger.info(f"Created survey: {title} by user {created_by}")
        return True, "Khảo sát được tạo thành công", survey.uuid
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating survey: {e}")
        return False, f"Lỗi tạo khảo sát: {str(e)}", None
    finally:
        session.close()

def get_surveys_db(user_id: Optional[int] = None, active_only: bool = True) -> List[Dict]:
    """Get surveys from database"""
    session = SessionLocal()
    try:
        query = session.query(Survey)
        
        if user_id:
            query = query.filter(Survey.created_by == user_id)
        
        if active_only:
            query = query.filter(Survey.active == True)
        
        surveys = query.order_by(desc(Survey.created_at)).all()
        return [survey.to_dict() for survey in surveys]
        
    except Exception as e:
        logger.error(f"Error getting surveys: {e}")
        return []
    finally:
        session.close()

def get_survey_by_uuid_db(survey_uuid: str) -> Optional[Dict]:
    """Get survey by UUID"""
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.uuid == survey_uuid).first()
        return survey.to_dict() if survey else None
    except Exception as e:
        logger.error(f"Error getting survey by UUID: {e}")
        return None
    finally:
        session.close()

def update_survey_db(survey_uuid: str, title: str, description: str, questions: List[Dict]) -> tuple[bool, str]:
    """Update an existing survey"""
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.uuid == survey_uuid).first()
        if not survey:
            return False, "Khảo sát không tồn tại"
        
        survey.title = title
        survey.description = description
        survey.questions = questions
        survey.updated_at = datetime.now()
        
        session.commit()
        # Invalidate cache after update
        try:
            from utils.cache_utils import invalidate_survey_cache
            invalidate_survey_cache(survey_uuid)
        except Exception:
            pass
        return True, "Cập nhật khảo sát thành công"

    except Exception as e:
        session.rollback()
        logger.error(f"Error updating survey: {e}")
        return False, f"Lỗi cập nhật khảo sát: {str(e)}"
    finally:
        session.close()

# Response Management Functions
def save_response_db(survey_uuid: str, response_data: Dict, user_id: Optional[int] = None, 
                    ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> tuple[bool, str]:
    """Save survey response to database"""
    session = SessionLocal()
    try:
        # Get survey
        survey = session.query(Survey).filter(Survey.uuid == survey_uuid).first()
        if not survey:
            return False, "Khảo sát không tồn tại"
        
        if not survey.active:
            return False, "Khảo sát đã bị vô hiệu hóa"
        
        # Check response limit
        if survey.response_limit:
            current_responses = session.query(Response).filter(Response.survey_id == survey.id).count()
            if current_responses >= survey.response_limit:
                return False, "Khảo sát đã đạt giới hạn phản hồi"
        
        # Create response
        response = Response(
            survey_id=survey.id,
            response_data=response_data,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        session.add(response)
        session.commit()

        # Cache-aside: invalidate stale cache after write
        try:
            from utils.cache_utils import invalidate_survey_cache
            invalidate_survey_cache(survey_uuid)
        except Exception:
            pass

        logger.info(f"Saved response for survey {survey_uuid}")
        return True, "Phản hồi được lưu thành công"

    except Exception as e:
        session.rollback()
        logger.error(f"Error saving response: {e}")
        return False, f"Lỗi lưu phản hồi: {str(e)}"
    finally:
        session.close()

def get_responses_db(survey_uuid: str) -> List[Dict]:
    """Get responses for a survey"""
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.uuid == survey_uuid).first()
        if not survey:
            return []
        
        responses = session.query(Response).filter(Response.survey_id == survey.id).order_by(desc(Response.submitted_at)).all()
        return [response.to_dict() for response in responses]
        
    except Exception as e:
        logger.error(f"Error getting responses: {e}")
        return []
    finally:
        session.close()

# Admin Functions
def create_default_admin():
    """Create default admin user if no admin exists"""
    session = SessionLocal()
    try:
        # Check if any admin exists
        admin_count = session.query(User).filter(User.role == "admin").count()
        
        if admin_count == 0:
            # Create default admin
            admin_user = User(
                username="admin",
                email="admin@survey.app",
                password_hash=hash_password("admin123"),
                role="admin",
                active=True
            )
            
            session.add(admin_user)
            session.commit()
            logger.info("Created default admin user")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default admin: {e}")
    finally:
        session.close()

def change_password_db(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Đổi mật khẩu người dùng"""
    session = SessionLocal()
    try:
        if len(new_password) < 6:
            return False, "Mật khẩu mới phải có ít nhất 6 ký tự"

        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False, "Người dùng không tồn tại"

        if user.password_hash != hash_password(old_password):
            return False, "Mật khẩu hiện tại không đúng"

        user.password_hash = hash_password(new_password)
        session.commit()
        return True, "Đổi mật khẩu thành công"

    except Exception as e:
        session.rollback()
        logger.error(f"Error changing password: {e}")
        return False, f"Lỗi đổi mật khẩu: {str(e)}"
    finally:
        session.close()


def get_system_stats_db() -> Dict[str, Any]:
    """Get system statistics"""
    session = SessionLocal()
    try:
        total_users = session.query(User).count()
        active_users = session.query(User).filter(User.active == True).count()
        total_surveys = session.query(Survey).count()
        active_surveys = session.query(Survey).filter(Survey.active == True).count()
        total_responses = session.query(Response).count()
        
        # Recent activity
        recent_surveys = session.query(Survey).order_by(desc(Survey.created_at)).limit(5).all()
        recent_responses = session.query(Response).order_by(desc(Response.submitted_at)).limit(10).all()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "admin_count": session.query(User).filter(User.role == "admin").count()
            },
            "surveys": {
                "total": total_surveys,
                "active": active_surveys
            },
            "responses": {
                "total": total_responses
            },
            "recent_activity": {
                "surveys": [s.to_dict() for s in recent_surveys],
                "responses": [r.to_dict() for r in recent_responses]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {}
    finally:
        session.close()