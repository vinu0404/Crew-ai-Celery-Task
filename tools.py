import os
from dotenv import load_dotenv
load_dotenv()

from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import Type
import PyPDF2

# Creating search tool
search_tool = SerperDevTool()

class BloodTestReportInput(BaseModel):
    """Input schema for BloodTestReportTool."""
    path: str = Field(description="Path to the PDF file")

class BloodTestReportTool(BaseTool):
    name: str = "blood_test_report_reader"
    description: str = "Tool to read and extract text from blood test PDF reports. Always provide the full path to the PDF file."
    args_schema: Type[BaseModel] = BloodTestReportInput

    def _run(self, path: str) -> str:
        """Tool to read data from a PDF file
        
        Args:
            path (str): Path of the PDF file
            
        Returns:
            str: Full Blood Test report content
        """
        try:
            if not path:
                return "Error: No file path provided"
                
            if not os.path.exists(path):
                return f"Error: File not found at path {path}. Please check if the file exists and the path is correct."
            
            full_report = ""
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if len(pdf_reader.pages) == 0:
                    return "Error: PDF file appears to be empty (no pages found)"
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    content = page.extract_text()
                    
                    # Clean and format the report data
                    while "\n\n" in content:
                        content = content.replace("\n\n", "\n")
                    
                    full_report += content + "\n"
            
            if not full_report.strip():
                return "Error: Could not extract text from PDF. The file might be empty, password-protected, or contain only images."
                
            return full_report
            
        except FileNotFoundError:
            return f"Error: File not found at path {path}"
        except PermissionError:
            return f"Error: Permission denied accessing file at path {path}"
        except Exception as e:
            return f"Error reading PDF file: {str(e)}"

class NutritionAnalysisInput(BaseModel):
    """Input schema for NutritionTool."""
    blood_report_data: str = Field(description="Blood report data to analyze")

class NutritionTool(BaseTool):
    name: str = "nutrition_analyzer"
    description: str = "Tool to analyze blood report data and provide nutrition recommendations"
    args_schema: Type[BaseModel] = NutritionAnalysisInput

    def _run(self, blood_report_data: str) -> str:
        """Analyze blood report and provide nutrition recommendations
        
        Args:
            blood_report_data (str): Blood report data
            
        Returns:
            str: Nutrition analysis and recommendations
        """
        try:
            # Process and analyze the blood report data
            processed_data = blood_report_data.strip()
            
            if not processed_data:
                return "Error: No blood report data provided for nutrition analysis"
            
            # Basic nutrition analysis based on common blood markers
            recommendations = []
            
            # Check for common deficiencies
            if "hemoglobin" in processed_data.lower() or "hgb" in processed_data.lower():
                recommendations.append("- Monitor iron levels and include iron-rich foods like spinach, lean meats, and legumes")
            
            if "vitamin d" in processed_data.lower():
                recommendations.append("- Consider vitamin D supplementation and foods like fatty fish, fortified milk")
            
            if "cholesterol" in processed_data.lower():
                recommendations.append("- Focus on heart-healthy diet with omega-3 rich foods, limit saturated fats")
            
            if "glucose" in processed_data.lower() or "sugar" in processed_data.lower():
                recommendations.append("- Monitor carbohydrate intake, choose complex carbs over simple sugars")
            
            if not recommendations:
                recommendations.append("- Maintain a balanced diet with adequate fruits, vegetables, and whole grains")
                recommendations.append("- Stay hydrated and limit processed foods")
            
            result = "NUTRITION ANALYSIS:\n" + "\n".join(recommendations)
            result += "\n\nNote: Please consult with a healthcare provider for personalized nutrition advice."
            
            return result
            
        except Exception as e:
            return f"Error in nutrition analysis: {str(e)}"

class ExercisePlanInput(BaseModel):
    """Input schema for ExerciseTool."""
    blood_report_data: str = Field(description="Blood report data to analyze for exercise planning")

class ExerciseTool(BaseTool):
    name: str = "exercise_planner"
    description: str = "Tool to create exercise recommendations based on blood report data"
    args_schema: Type[BaseModel] = ExercisePlanInput

    def _run(self, blood_report_data: str) -> str:
        """Create exercise plan based on blood report
        
        Args:
            blood_report_data (str): Blood report data
            
        Returns:
            str: Exercise recommendations
        """
        try:
            processed_data = blood_report_data.strip()
            
            if not processed_data:
                return "Error: No blood report data provided for exercise planning"
            
            # Basic exercise recommendations
            recommendations = []
            
            # General recommendations
            recommendations.append("EXERCISE RECOMMENDATIONS:")
            recommendations.append("- Start with 150 minutes of moderate-intensity aerobic activity per week")
            recommendations.append("- Include 2-3 strength training sessions per week")
            recommendations.append("- Begin gradually and increase intensity over time")
            
            # Specific recommendations based on markers
            if "cholesterol" in processed_data.lower():
                recommendations.append("- Focus on cardiovascular exercises like walking, swimming, or cycling")
            
            if "glucose" in processed_data.lower() or "diabetes" in processed_data.lower():
                recommendations.append("- Include both aerobic and resistance training to help with glucose control")
            
            if "blood pressure" in processed_data.lower() or "hypertension" in processed_data.lower():
                recommendations.append("- Avoid heavy weightlifting, focus on moderate cardio and flexibility exercises")
            
            recommendations.append("\nIMPORTANT: Consult with your healthcare provider before starting any new exercise program.")
            
            return "\n".join(recommendations)
            
        except Exception as e:
            return f"Error in exercise planning: {str(e)}"

# Create tool instances
blood_test_tool = BloodTestReportTool()
nutrition_tool = NutritionTool()
exercise_tool = ExerciseTool()