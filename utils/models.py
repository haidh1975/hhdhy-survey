from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from utils.database import Base
import uuid

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 'admin' or 'user'
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    surveys = relationship("Survey", back_populates="creator", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class Survey(Base):
    """Survey model for storing survey definitions"""
    __tablename__ = "surveys"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(JSON, nullable=False)  # Store questions as JSON
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    active = Column(Boolean, default=True, nullable=False)
    
    # Survey settings
    allow_anonymous = Column(Boolean, default=True)
    multiple_responses = Column(Boolean, default=True)
    response_limit = Column(Integer, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="surveys")
    responses = relationship("Response", back_populates="survey", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Survey(id={self.id}, title='{self.title}', created_by={self.created_by})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "title": self.title,
            "description": self.description,
            "questions": self.questions,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "active": self.active,
            "allow_anonymous": self.allow_anonymous,
            "multiple_responses": self.multiple_responses,
            "response_limit": self.response_limit,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "response_count": len(self.responses) if self.responses else 0
        }

class Response(Base):
    """Response model for storing survey responses"""
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    response_data = Column(JSON, nullable=False)  # Store response data as JSON
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Response metadata
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    completion_time = Column(Integer, nullable=True)  # Time in seconds
    
    # Optional user association (for logged-in responses)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    survey = relationship("Survey", back_populates="responses")
    user = relationship("User")  # Optional relationship
    
    def __repr__(self):
        return f"<Response(id={self.id}, survey_id={self.survey_id}, submitted_at={self.submitted_at})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "response_data": self.response_data,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "completion_time": self.completion_time,
            "user_id": self.user_id
        }

# Create indexes for better performance
from sqlalchemy import Index

# Indexes for better query performance
Index('idx_surveys_created_by', Survey.created_by)
Index('idx_surveys_uuid', Survey.uuid)
Index('idx_surveys_active', Survey.active)
Index('idx_responses_survey_id', Response.survey_id)
Index('idx_responses_submitted_at', Response.submitted_at)
Index('idx_users_username', User.username)
Index('idx_users_email', User.email)
Index('idx_users_active', User.active)