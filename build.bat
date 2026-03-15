@echo off
echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Construyendo el .exe...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "TikTokRachas" ^
  --add-data "config.json;." ^
  main.py

echo.
echo Listo. El .exe está en la carpeta dist\
echo Copia el .exe a la raíz del proyecto (junto a data\ y config.json) para ejecutarlo.
pause
