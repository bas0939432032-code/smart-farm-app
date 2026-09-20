@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false
pause
