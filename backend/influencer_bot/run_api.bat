@echo off
echo Starting Influencer Finder API (PRODUCTION)...
echo.
echo API will be available at: http://localhost:8000
echo Docs at: http://localhost:8000/docs
echo.
echo NOTE: No auto-reload — running Playwright jobs will NOT be killed by file changes.
echo       For development with auto-reload, use run_api_dev.bat instead.
echo.
uvicorn main:app --host 0.0.0.0 --port 8000
pause
