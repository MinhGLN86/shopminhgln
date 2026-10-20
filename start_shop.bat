@echo off
title ShopMinhGLN Server + Ngrok
chcp 65001 >nul
echo ===================================================
echo     ShopMinhGLN - KHỞI ĐỘNG HỆ THỐNG SHOP VÀ NGROK
echo ===================================================
echo.
echo [1/2] Đang khởi động Flask Web Server (Port 5000)...
start "ShopMinhGLN Web Server" cmd /k "python app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Đang mở đường truyền Ngrok tĩnh cố định...
start "Ngrok Tunnel" cmd /k "ngrok.exe http --url=art-sterile-moocher.ngrok-free.dev 5000"

echo.
echo ===================================================
echo ĐÃ KHỞI CHẠY THÀNH CÔNG!
echo Link cố định của shop: https://art-sterile-moocher.ngrok-free.dev
echo ===================================================
echo.
pause
