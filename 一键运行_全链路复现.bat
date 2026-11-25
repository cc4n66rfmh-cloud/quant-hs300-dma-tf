@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   全链路复现：原始行情 - 信号 - 回测 - 指标 - 出图
echo   答辩演示用，证明系统有真实可运行内核
echo ============================================
echo.
"C:\Users\HUAWEI\AppData\Local\Programs\Python\Python312\python.exe" "全链路复现代码.py"
echo.
echo 运行结束，按任意键关闭窗口...
pause >nul
