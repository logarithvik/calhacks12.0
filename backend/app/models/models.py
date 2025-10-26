from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """User model for authentication and trial management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trials = relationship("Trial", back_populates="owner")


class Trial(Base):
    """Clinical trial protocol information"""
    __tablename__ = "trials"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    protocol_file_path = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)
    status = Column(String, default="uploaded")  # uploaded, processing, completed, error
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="trials")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generated_content = relationship("GeneratedContent", back_populates="trial", cascade="all, delete-orphan")


class GeneratedContent(Base):
    """Store generated summaries, infographics, and videos"""
    __tablename__ = "generated_content"
    
    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=False)
    
    # Content types: 'summary', 'infographic', 'video'
    content_type = Column(String, nullable=False)
    
    # Extracted/generated data
    # For summaries: plain text stored here and optionally as a separate .txt file
    content_text = Column(Text, nullable=True)
    content_file_path = Column(String, nullable=True)  # Path to a plain-text file (e.g., uploads/generated/summary_.. .txt)

    # For infographics and videos
    file_path = Column(String, nullable=True)
    file_url = Column(String, nullable=True)  # Public URL if hosted
    
    # Metadata
    is_approved = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    trial = relationship("Trial", back_populates="generated_content")
