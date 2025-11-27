REM
set UI_DIR=ui

REM 
set OUT_DIR=py_ui

REM Loop through all .ui files and convert them
for %%f in (%UI_DIR%\*.ui) do (
    echo Compiling %%f...
    pyuic6 "%%f" -o "%OUT_DIR%\%%~nf.py"
)