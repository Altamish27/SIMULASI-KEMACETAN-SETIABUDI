@echo off
cd /d "%~dp0"
echo Menyalakan simulasi 3D... browser akan terbuka otomatis (http://127.0.0.1:8000)
echo Tutup jendela ini untuk menghentikan simulasi.
python bridge\server.py
pause
