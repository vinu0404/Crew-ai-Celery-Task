Write-Host "Starting Celery Worker for Blood Test Analyzer..." -ForegroundColor Green

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
    Write-Host "Error: blood_test_env environment not found!" -ForegroundColor Red
    Write-Host "Please run the full setup script first to create the environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} else {
    Write-Host "Environment blood_test_env found" -ForegroundColor Green
}

# Activate conda environment
Write-Host "Activating conda environment..." -ForegroundColor Yellow
conda activate blood_test_env
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error activating conda environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Environment activated successfully!" -ForegroundColor Green

# Check if Redis is running
Write-Host "Checking Redis connection..." -ForegroundColor Yellow
try {
    python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('Redis is connected')" 2>$null
    Write-Host "Redis is connected" -ForegroundColor Green
} catch {
    Write-Host "Error: Redis is not running!" -ForegroundColor Red
    Write-Host "Please start Redis first using Docker: docker run -d -p 6379:6379 redis:latest" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if required packages are installed
Write-Host "Checking required packages..." -ForegroundColor Yellow
try {
    python -c "import onnxruntime; print('onnxruntime is installed')" 2>$null
    Write-Host "onnxruntime is available" -ForegroundColor Green
} catch {
    Write-Host "Warning: onnxruntime not found. Installing..." -ForegroundColor Yellow
    try {
        conda install -c conda-forge onnxruntime -y
        Write-Host "onnxruntime installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install onnxruntime via conda. Trying pip..." -ForegroundColor Yellow
        pip install onnxruntime
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Celery Worker..." -ForegroundColor Green
Write-Host "Worker will process async analysis tasks" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the worker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Celery worker
try {
    celery -A celery_worker worker --loglevel=info --pool=solo
} catch {
    Write-Host "Error starting Celery worker" -ForegroundColor Red
    Write-Host "Make sure the celery_worker.py file exists and all dependencies are installed" -ForegroundColor Yellow
}

Read-Host "Press Enter to exit"