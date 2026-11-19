@echo off
cd /d "%~dp0"
echo Menjalankan analisis 4 skenario x 3 seed (sekitar 30-40 menit)...
python toolsatch.py
echo Selesai. Lihat resultsingkasan.md dan grafik di folder results.
pause
