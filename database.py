import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blood_analysis.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class BloodAnalysis(Base):
    __tablename__ = "blood_analyses"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float, nullable=True)
    status = Column(String, default="completed")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_analyses = Column(Integer, default=0)

def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database"""
    create_tables()
    print("Database initialized successfully!")