@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   日常展示：读取回测结果，秒出指标和净值图
echo ============================================
echo.
"C:\Users\HUAWEI\AppData\Local\Programs\Python\Python312\python.exe" main.py
echo.
echo 运行结束，按任意键关闭窗口...
pause >nul
