Write-Host "Starting Blood Test Report Analyzer..." -ForegroundColor Green

# Check if conda is installed
try {
    $condaVersion = conda --version 2>$null
    Write-Host "Conda found: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Conda is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Anaconda/Miniconda and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if conda environment exists
$envExists = conda info --envs | Select-String "blood_test_env"
if (-not $envExists) {
    Write-Host "Creating conda environment..." -ForegroundColor Yellow
    conda create -n blood_test_env python=3.10 -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating conda environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Environment blood_test_env already exists" -ForegroundColor Green
}

# Activate conda environment
Write-Host "Activating conda environment..." -ForegroundColor Yellow
conda activate blood_test_env
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error activating conda environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install requirements using conda and conda-forge
Write-Host "Installing requirements from conda-forge..." -ForegroundColor Yellow
conda install -c conda-forge fastapi uvicorn python-dotenv python-multipart redis-py sqlalchemy alembic pydantic onnxruntime tokenizers tqdm -y
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing conda packages" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install packages that might not be available in conda-forge using pip
Write-Host "Installing additional packages with pip..." -ForegroundColor Yellow
pip install crewai crewai-tools PyPDF2 langchain-community openai celery chromadb
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing pip packages" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create data directory
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data"
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
try {
    python -c "from database import init_db; init_db()"
} catch {
    Write-Host "Warning: Database initialization failed" -ForegroundColor Yellow
}

# Check if Redis is running
Write-Host "Checking Redis connection..." -ForegroundColor Yellow
try {
    python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('Redis is running')" 2>$null
    Write-Host "Redis is running" -ForegroundColor Green
} catch {
    Write-Host "Warning: Redis is not running. Async processing will not work." -ForegroundColor Yellow
    Write-Host "Please start Redis using Docker: docker run -d -p 6379:6379 redis:latest" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting the application..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Read-Host "Press Enter to exit"