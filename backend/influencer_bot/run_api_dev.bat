@echo off
echo Starting Influencer Finder API (DEV MODE)...
echo.
echo API will be available at: http://localhost:8000
echo Docs at: http://localhost:8000/docs
echo.
echo Auto-reload ON (excludes output/ directory to protect running jobs)
echo.
uvicorn main:app --reload --reload-exclude "output/*" --reload-exclude "*.csv" --reload-exclude "instagram_session.json" --host 0.0.0.0 --port 8000
pause
