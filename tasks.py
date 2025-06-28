from crewai import Task
from agents import medical_doctor, verifier_agent, nutrition_specialist, exercise_specialist
from tools import blood_test_tool, nutrition_tool, exercise_tool

# Task to verify and read blood test report
verification_task = Task(
    description="""
    Verify that the uploaded document is a valid blood test report and extract all relevant information.
    
    The file path is provided in the context: {file_path}
    
    Steps:
    1. Read the uploaded document using the blood test report tool with the provided file path
    2. Verify it contains legitimate blood test results with proper formatting
    3. Extract key laboratory values, reference ranges, and any abnormal findings
    4. Identify the type of blood panel (CBC, CMP, lipid panel, etc.)
    5. Flag any concerns about document authenticity or completeness
    
    Focus on: Laboratory values, reference ranges, test dates, patient information (if present)
    
    Use the blood_test_report_reader tool with the exact file path provided in the context.
    """,
    expected_output="""
    A comprehensive verification report containing:
    - Document validation status (Valid/Invalid blood test report)
    - Extracted laboratory values with their reference ranges
    - List of abnormal findings (if any)
    - Type of blood panel(s) included
    - Any data quality concerns or missing information
    - Formatted summary of all relevant medical data
    """,
    agent=verifier_agent,
    tools=[blood_test_tool]
)

# Main medical analysis task
medical_analysis_task = Task(
    description="""
    Analyze the verified blood test report and provide professional medical insights based on the user's query: {query}
    
    The file path is provided in the context: {file_path}
    
    Tasks:
    1. Use the blood_test_report_reader tool with the provided file path to read the report
    2. Interpret laboratory values in clinical context
    3. Identify any abnormal results and their potential clinical significance
    4. Address the specific user query with relevant medical information
    5. Provide educational information about the blood tests performed
    6. Suggest appropriate follow-up actions if needed
    
    Remember to:
    - Use evidence-based medical knowledge
    - Explain medical terms in understandable language
    - Emphasize the importance of healthcare provider consultation
    - Be conservative and safety-focused in recommendations
    """,
    expected_output="""
    A comprehensive medical analysis report including:
    - Summary of blood test results with interpretation
    - Identification and explanation of any abnormal values
    - Clinical significance of findings
    - Direct response to the user's specific query
    - Educational information about relevant blood markers
    - Professional recommendations for follow-up care
    - Clear disclaimer about consulting healthcare providers
    - Well-structured, easy-to-understand format
    """,
    agent=medical_doctor,
    tools=[blood_test_tool],
    context=[verification_task]
)

# Nutrition analysis task
nutrition_analysis_task = Task(
    description="""
    Analyze the blood test results and provide evidence-based nutritional recommendations.
    
    Focus areas:
    1. Review blood markers related to nutrition (iron, B12, folate, vitamin D, etc.)
    2. Assess metabolic markers (glucose, lipids, kidney function)
    3. Identify potential nutritional deficiencies or concerns
    4. Provide specific dietary recommendations based on findings
    5. Suggest appropriate nutritional supplements if indicated
    6. Consider any contraindications or special dietary needs
    """,
    expected_output="""
    A detailed nutritional analysis containing:
    - Assessment of nutrition-related blood markers
    - Identification of potential deficiencies or imbalances
    - Specific dietary recommendations with food examples
    - Supplement suggestions with dosage considerations
    - Meal planning guidance
    - Foods to emphasize and foods to limit
    - Timeline for nutritional interventions
    - Recommendation to work with registered dietitian
    """,
    agent=nutrition_specialist,
    tools=[nutrition_tool],
    context=[verification_task, medical_analysis_task]
)

# Exercise planning task
exercise_planning_task = Task(
    description="""
    Develop safe and effective exercise recommendations based on the blood test results and overall health status.
    
    Considerations:
    1. Review cardiovascular risk markers (cholesterol, triglycerides, blood pressure indicators)
    2. Assess metabolic health (glucose, HbA1c if available)
    3. Check for markers that might affect exercise capacity
    4. Consider any contraindications to specific types of exercise
    5. Develop progressive exercise recommendations
    6. Include both cardiovascular and strength training components
    """,
    expected_output="""
    A comprehensive exercise plan including:
    - Assessment of exercise readiness based on blood markers
    - Specific cardiovascular exercise recommendations
    - Strength training guidelines
    - Flexibility and mobility recommendations
    - Exercise intensity and frequency guidelines
    - Progression plan over time
    - Safety considerations and contraindications
    - Monitoring recommendations during exercise
    - Emphasis on medical clearance requirements
    """,
    agent=exercise_specialist,
    tools=[exercise_tool],
    context=[verification_task, medical_analysis_task]
)

# Consolidated help task (main task for simple requests)
help_patients_task = Task(
    description="""
    Provide comprehensive analysis of the blood test report to address the user's query: {query}
    
    The file path is available in the context: {file_path}
    
    This is the main task that coordinates the analysis process:
    1. Use the blood_test_report_reader tool with the provided file path to read and verify the blood test report
    2. Interpret the laboratory results professionally
    3. Address the specific user query
    4. Provide relevant health insights and recommendations
    5. Include appropriate medical disclaimers
    
    IMPORTANT: When using the blood_test_report_reader tool, make sure to pass the correct file path from the context.
    
    Ensure the response is:
    - Medically accurate and evidence-based
    - Easy to understand for non-medical users
    - Appropriately cautious with recommendations
    - Encouraging of proper medical follow-up
    """,
    expected_output="""
    A professional medical report containing:
    - Clear interpretation of blood test results
    - Direct answer to the user's specific question
    - Explanation of any abnormal findings
    - General health recommendations based on results
    - Appropriate medical disclaimers
    - Suggestion to consult healthcare providers
    - Well-organized and readable format
    """,
    agent=medical_doctor,
    tools=[blood_test_tool]
)