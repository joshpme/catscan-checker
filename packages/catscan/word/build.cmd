@echo off
setlocal enabledelayedexpansion

:: Create a virtual environment without pip
python -m venv virtualenv

:: Activate the virtual environment
call virtualenv\Scripts\activate

:: Install requirements.txt into the virtual environment
pip install -r requirements.txt

:: Deactivate the virtual environment
deactivate