@echo off

chcp 65001

cd files
echo ======================== install python3.12 ===========================
call python-3.12.4-amd64.exe /passive InstallAllUsers=1 SimpleInstall=1
timeout /t 3 /nobreak
REM setx /M Path "%Path%;%ProgramFiles%\Python312"
setx /m Path "%Path%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"
timeout /t 3 /nobreak
echo ======================== refresh environment ==============================
cd ..
call refreshenv.bat
echo ======================== install poetry ===========================
call pip install -i https://pypi.tuna.tsinghua.edu.cn/simple poetry
echo ======================== install dependencies =============================
call poetry install
echo ======================== start YTYOUNB server ===========================
cd ytautocontrol
start "YTYOUNB" /min poetry run python main.py

