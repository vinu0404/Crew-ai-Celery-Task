"""
API Client for Blood Test Report Analyzer
Example usage and testing script
"""

import requests
import time
import json
from pathlib import Path

class BloodTestAnalyzerClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def health_check(self):
        """Check if the API is running"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"error": "API is not running"}
    
    def analyze_sync(self, file_path: str, query: str = "Summarize my blood test report"):
        """Analyze blood test report synchronously"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'query': query, 'async_processing': False}
            
            response = requests.post(f"{self.base_url}/analyze", files=files, data=data)
            return response.json()
    
    def analyze_async(self, file_path: str, query: str = "Summarize my blood test report"):
        """Start asynchronous analysis"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'query': query, 'async_processing': True}
            
            response = requests.post(f"{self.base_url}/analyze", files=files, data=data)
            return response.json()
    
    def comprehensive_analysis(self, file_path: str, query: str = "Provide comprehensive analysis"):
        """Start comprehensive analysis with all specialists"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'query': query}
            
            response = requests.post(f"{self.base_url}/analyze/comprehensive", files=files, data=data)
            return response.json()
    
    def get_task_status(self, task_id: str):
        """Get status of async task"""
        response = requests.get(f"{self.base_url}/task/{task_id}")
        return response.json()
    
    def wait_for_task(self, task_id: str, timeout: int = 300):
        """Wait for async task to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            print(f"Task status: {status['status']}")
            time.sleep(5)
        
        return {"error": "Task timeout"}
    
    def get_analysis_history(self, limit: int = 10, offset: int = 0):
        """Get analysis history"""
        response = requests.get(f"{self.base_url}/analysis/history?limit={limit}&offset={offset}")
        return response.json()
    
    def get_analysis_result(self, analysis_id: int):
        """Get detailed analysis result"""
        response = requests.get(f"{self.base_url}/analysis/{analysis_id}")
        return response.json()
    
    def get_statistics(self):
        """Get system statistics"""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()

def example_usage():
    """Example usage of the API client"""
    client = BloodTestAnalyzerClient()
    
    # Health check
    print("=== Health Check ===")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # Note: You need to have a sample PDF file to test
    sample_file = "data/sample.pdf"
    
    if not Path(sample_file).exists():
        print(f"\nError: Sample file {sample_file} not found")
        print("Please add a sample blood test PDF to test the API")
        return
    
    # Synchronous analysis
    print("\n=== Synchronous Analysis ===")
    sync_result = client.analyze_sync(sample_file, "What are my cholesterol levels?")
    print(json.dumps(sync_result, indent=2))
    
    # Asynchronous analysis
    print("\n=== Asynchronous Analysis ===")
    async_result = client.analyze_async(sample_file, "Are there any abnormal values?")
    print(f"Task ID: {async_result.get('task_id')}")
    
    if 'task_id' in async_result:
        # Wait for completion
        final_result = client.wait_for_task(async_result['task_id'])
        print(json.dumps(final_result, indent=2))
    
    # Get statistics
    print("\n=== Statistics ===")
    stats = client.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Get history
    print("\n=== Analysis History ===")
    history = client.get_analysis_history(limit=5)
    print(json.dumps(history, indent=2))

if __name__ == "__main__":
    example_usage()