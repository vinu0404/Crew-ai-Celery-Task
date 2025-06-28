from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import time
import shutil
from typing import Optional
from pydantic import BaseModel
import uvicorn
from crewai import Crew, Process
from agents import medical_doctor
from tasks import help_patients_task
from database import get_db, init_db, BloodAnalysis
from celery_worker import analyze_blood_report_task, comprehensive_analysis_task

# Initialize database
init_db()

app = FastAPI(title="Blood Test Report Analyzer", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    analysis_id: Optional[int] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    meta: Optional[dict] = None

def run_crew_sync(query: str, file_path: str):
    """Synchronous crew execution for immediate processing"""
    
    # Verify file exists before processing
    if not os.path.exists(file_path):
        raise Exception(f"File not found at path: {file_path}")
    
    medical_crew = Crew(
        agents=[medical_doctor],
        tasks=[help_patients_task],
        process=Process.sequential,
        verbose=False
    )
    
    # Pass both query and file_path to the crew
    result = medical_crew.kickoff({
        'query': query,
        'file_path': file_path
    })
    return result

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Blood Test Report Analyzer API v2.0 is running",
        "features": [
            "Synchronous and asynchronous analysis",
            "Database storage",
            "Celery queue processing",
            "Comprehensive multi-agent analysis"
        ]
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "celery": "available",
        "timestamp": time.time()
    }

@app.post("/analyze", response_model=dict)
async def analyze_blood_report(
    file: UploadFile = File(...),
    query: str = Form(default="Summarize my blood test report"),
    async_processing: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    """
    Analyze blood test report with option for sync or async processing
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique filename with absolute path
    file_id = str(uuid.uuid4())
    # Use absolute path to ensure Celery worker can find the file
    data_dir = os.path.abspath("data")
    file_path = os.path.join(data_dir, f"blood_test_report_{file_id}.pdf")
    
    try:
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Save uploaded file using shutil for better file handling
        with open(file_path, "wb") as f:
            # Reset file position to beginning
            await file.seek(0)
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            f.write(content)
        
        # Verify file was saved correctly
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
            
        # Log file details for debugging
        file_size = os.path.getsize(file_path)
        print(f"File saved: {file_path}, size: {file_size} bytes")
        
        # Validate query
        if not query or query.strip() == "":
            query = "Summarize my blood test report"
        
        if async_processing:
            # Async processing with Celery
            # Pass absolute file path to ensure Celery worker can access it
            task = analyze_blood_report_task.delay(query.strip(), file_path, file.filename)
            return {
                "status": "accepted",
                "message": "Analysis started. Use the task_id to check status.",
                "task_id": task.id,
                "query": query,
                "filename": file.filename,
                "processing_type": "async",
                "file_path": file_path  # Include for debugging
            }
        else:
            # Synchronous processing
            start_time = time.time()
            
            try:
                result = run_crew_sync(query=query.strip(), file_path=file_path)
                processing_time = time.time() - start_time
                
                # Save to database
                analysis = BloodAnalysis(
                    filename=file.filename,
                    query=query,
                    analysis_result=str(result),
                    processing_time=processing_time,
                    status="completed"
                )
                db.add(analysis)
                db.commit()
                db.refresh(analysis)
                
                return {
                    "status": "success",
                    "message": "Analysis completed successfully",
                    "query": query,
                    "analysis": str(result),
                    "filename": file.filename,
                    "processing_time": processing_time,
                    "analysis_id": analysis.id,
                    "processing_type": "sync"
                }
                
            except Exception as e:
                # Save error to database
                analysis = BloodAnalysis(
                    filename=file.filename,
                    query=query,
                    analysis_result=f"Error: {str(e)}",
                    processing_time=time.time() - start_time,
                    status="failed"
                )
                db.add(analysis)
                db.commit()
                raise HTTPException(status_code=500, detail=f"Error processing blood report: {str(e)}")
            
            finally:
                # Clean up uploaded file for sync processing only
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if there was an error and async processing was not requested
        if not async_processing and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/analyze/comprehensive", response_model=dict)
async def comprehensive_analysis(
    file: UploadFile = File(...),
    query: str = Form(default="Provide comprehensive analysis with nutrition and exercise recommendations"),
    db: Session = Depends(get_db)
):
    """
    Comprehensive analysis with all specialists (always async due to complexity)
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique filename with absolute path
    file_id = str(uuid.uuid4())
    data_dir = os.path.abspath("data")
    file_path = os.path.join(data_dir, f"blood_test_report_{file_id}.pdf")
    
    try:
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            await file.seek(0)
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            f.write(content)
        
        # Verify file was saved correctly
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        # Validate query
        if not query or query.strip() == "":
            query = "Provide comprehensive analysis with nutrition and exercise recommendations"
        
        # Start comprehensive analysis task
        task = comprehensive_analysis_task.delay(query.strip(), file_path, file.filename)
        
        return {
            "status": "accepted",
            "message": "Comprehensive analysis started. This may take several minutes.",
            "task_id": task.id,
            "query": query,
            "filename": file.filename,
            "processing_type": "comprehensive",
            "estimated_time": "3-5 minutes"
        }
        
    except Exception as e:
        # Clean up file if there was an error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error starting comprehensive analysis: {str(e)}")

@app.get("/task/{task_id}", response_model=dict)
async def get_task_status(task_id: str):
    """
    Get the status and result of an async task
    """
    try:
        from celery_worker import celery_app
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task.state == 'PROGRESS':
            response = {
                "task_id": task_id,
                "status": "processing",
                "message": "Task is being processed",
                "meta": task.info
            }
        elif task.state == 'SUCCESS':
            response = {
                "task_id": task_id,
                "status": "completed",
                "result": task.result
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info)
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving task status: {str(e)}")

@app.get("/analysis/history")
async def get_analysis_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get analysis history from database
    """
    try:
        analyses = db.query(BloodAnalysis)\
                    .order_by(BloodAnalysis.created_at.desc())\
                    .offset(offset)\
                    .limit(limit)\
                    .all()
        
        total_count = db.query(BloodAnalysis).count()
        
        return {
            "total_count": total_count,
            "analyses": [
                {
                    "id": analysis.id,
                    "filename": analysis.filename,
                    "query": analysis.query,
                    "status": analysis.status,
                    "created_at": analysis.created_at,
                    "processing_time": analysis.processing_time
                }
                for analysis in analyses
            ],
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis history: {str(e)}")

@app.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get detailed analysis result by ID
    """
    try:
        analysis = db.query(BloodAnalysis).filter(BloodAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "id": analysis.id,
            "filename": analysis.filename,
            "query": analysis.query,
            "analysis_result": analysis.analysis_result,
            "status": analysis.status,
            "created_at": analysis.created_at,
            "processing_time": analysis.processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")

@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Delete analysis record
    """
    try:
        analysis = db.query(BloodAnalysis).filter(BloodAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        db.delete(analysis)
        db.commit()
        
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting analysis: {str(e)}")

@app.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get system statistics
    """
    try:
        total_analyses = db.query(BloodAnalysis).count()
        completed_analyses = db.query(BloodAnalysis).filter(BloodAnalysis.status == "completed").count()
        failed_analyses = db.query(BloodAnalysis).filter(BloodAnalysis.status == "failed").count()
        
        # Average processing time for completed analyses
        avg_processing_time = db.query(BloodAnalysis.processing_time)\
                               .filter(BloodAnalysis.status == "completed")\
                               .filter(BloodAnalysis.processing_time.isnot(None))\
                               .all()
        
        avg_time = sum([t[0] for t in avg_processing_time]) / len(avg_processing_time) if avg_processing_time else 0
        
        return {
            "total_analyses": total_analyses,
            "completed_analyses": completed_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0,
            "average_processing_time": round(avg_time, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)