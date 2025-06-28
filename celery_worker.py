import os
import time
from celery import Celery
from dotenv import load_dotenv
from crewai import Crew, Process
from agents import medical_doctor, nutrition_specialist, exercise_specialist, verifier_agent
from tasks import help_patients_task, verification_task, medical_analysis_task, nutrition_analysis_task, exercise_planning_task
from database import SessionLocal, BloodAnalysis
from datetime import datetime

load_dotenv()

# Initialize Celery
celery_app = Celery(
    "blood_analysis_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)

@celery_app.task(bind=True)
def analyze_blood_report_task(self, query: str, file_path: str, filename: str):
    """
    Celery task to analyze blood test report
    """
    start_time = time.time()
    
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Starting analysis...', 'file_path': file_path})
        
        # Debug: Log file path and check existence
        print(f"Celery worker: Processing file at path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        # Verify file exists with detailed error reporting
        if not os.path.exists(file_path):
            # Try to list files in the directory to help with debugging
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path):
                files_in_dir = os.listdir(dir_path)
                error_msg = f"File not found at path: {file_path}. Files in directory {dir_path}: {files_in_dir}"
            else:
                error_msg = f"File not found at path: {file_path}. Directory {dir_path} does not exist."
            
            print(error_msg)
            raise Exception(error_msg)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception(f"File at {file_path} is empty")
        
        # Create medical analysis crew
        medical_crew = Crew(
            agents=[medical_doctor],
            tasks=[help_patients_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Update status
        self.update_state(state='PROGRESS', meta={'status': 'Running medical analysis...', 'file_size': file_size})
        
        # Execute the crew with file_path in context
        result = medical_crew.kickoff({
            'query': query,
            'file_path': file_path
        })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Save to database
        db = SessionLocal()
        try:
            analysis = BloodAnalysis(
                filename=filename,
                query=query,
                analysis_result=str(result),
                processing_time=processing_time,
                status="completed"
            )
            db.add(analysis)
            db.commit()
            analysis_id = analysis.id
        except Exception as db_error:
            print(f"Database error: {db_error}")
            analysis_id = None
        finally:
            db.close()
        
        # Clean up the uploaded file after processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Successfully cleaned up file: {file_path}")
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up file {file_path}: {cleanup_error}")
        
        return {
            "status": "success",
            "query": query,
            "analysis": str(result),
            "filename": filename,
            "processing_time": processing_time,
            "analysis_id": analysis_id
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"Error in analyze_blood_report_task: {error_message}")
        
        # Save error to database
        db = SessionLocal()
        try:
            analysis = BloodAnalysis(
                filename=filename,
                query=query,
                analysis_result=f"Error: {error_message}",
                processing_time=time.time() - start_time,
                status="failed"
            )
            db.add(analysis)
            db.commit()
        except Exception as db_error:
            print(f"Database error while saving failure: {db_error}")
        finally:
            db.close()
        
        # Clean up the uploaded file even on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up file after error: {file_path}")
        except Exception as cleanup_error:
            print(f"Could not clean up file after error: {cleanup_error}")
            
        return {
            "status": "error",
            "error": error_message,
            "filename": filename
        }

@celery_app.task(bind=True)
def comprehensive_analysis_task(self, query: str, file_path: str, filename: str):
    """
    Comprehensive analysis with all specialists
    """
    start_time = time.time()
    
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Starting comprehensive analysis...', 'file_path': file_path})
        
        # Debug: Log file path and check existence
        print(f"Comprehensive analysis: Processing file at path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        # Verify file exists with detailed error reporting
        if not os.path.exists(file_path):
            # Try to list files in the directory to help with debugging
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path):
                files_in_dir = os.listdir(dir_path)
                error_msg = f"File not found at path: {file_path}. Files in directory {dir_path}: {files_in_dir}"
            else:
                error_msg = f"File not found at path: {file_path}. Directory {dir_path} does not exist."
            
            print(error_msg)
            raise Exception(error_msg)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception(f"File at {file_path} is empty")
        
        # Create comprehensive crew with all specialists
        comprehensive_crew = Crew(
            agents=[verifier_agent, medical_doctor, nutrition_specialist, exercise_specialist],
            tasks=[verification_task, medical_analysis_task, nutrition_analysis_task, exercise_planning_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Update status
        self.update_state(state='PROGRESS', meta={'status': 'Running comprehensive analysis with all specialists...', 'file_size': file_size})
        
        # Execute the crew with file_path in context
        result = comprehensive_crew.kickoff({
            'query': query,
            'file_path': file_path
        })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Save to database
        db = SessionLocal()
        try:
            analysis = BloodAnalysis(
                filename=filename,
                query=f"Comprehensive: {query}",
                analysis_result=str(result),
                processing_time=processing_time,
                status="completed"
            )
            db.add(analysis)
            db.commit()
            analysis_id = analysis.id
        except Exception as db_error:
            print(f"Database error: {db_error}")
            analysis_id = None
        finally:
            db.close()
        
        # Clean up the uploaded file after processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Successfully cleaned up file: {file_path}")
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up file {file_path}: {cleanup_error}")
        
        return {
            "status": "success",
            "query": query,
            "analysis": str(result),
            "filename": filename,
            "processing_time": processing_time,
            "analysis_id": analysis_id,
            "analysis_type": "comprehensive"
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"Error in comprehensive_analysis_task: {error_message}")
        
        # Save error to database
        db = SessionLocal()
        try:
            analysis = BloodAnalysis(
                filename=filename,
                query=f"Comprehensive: {query}",
                analysis_result=f"Error: {error_message}",
                processing_time=time.time() - start_time,
                status="failed"
            )
            db.add(analysis)
            db.commit()
        except Exception as db_error:
            print(f"Database error while saving failure: {db_error}")
        finally:
            db.close()
        
        # Clean up the uploaded file even on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up file after error: {file_path}")
        except Exception as cleanup_error:
            print(f"Could not clean up file after error: {cleanup_error}")
            
        return {
            "status": "error",
            "error": error_message,
            "filename": filename,
            "analysis_type": "comprehensive"
        }

if __name__ == "__main__":
    celery_app.start()