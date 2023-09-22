@echo off
setlocal enabledelayedexpansion

python -m venv virtualenv
call venv\Scripts\activate
pip install -r requirements.txt
deactivate