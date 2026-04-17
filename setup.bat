@echo off
echo Setting up environment...

python -m venv venv

call venv\Scripts\activate

python -m pip install --upgrade pip

pip install -r requirements.txt

echo.
echo Setup complete!
echo Run:
echo venv\Scripts\activate
echo python simulation.py

pause