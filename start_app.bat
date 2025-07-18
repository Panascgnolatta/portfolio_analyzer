@echo off
REM Anaconda仮想環境のパス。anaconda3がC:\anaconda3にある場合
call C:\anaconda3\Scripts\activate.bat pa-env
cd /d C:\dev\pyqt_portfolio_analyzer
python -m pyqt_portfolio_analyzer
pause
