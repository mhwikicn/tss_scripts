@echo off
setlocal enabledelayedexpansion


if "%~1"=="" (
    echo Usage: %~nx0 "the folder path where sp part files are"
    echo e.g.: %~nx0 "C:\folder_contains_sp_part_files"
    echo or just drag the folder to this batch file
    pause
    exit /b 1
)
set "target_path=%~f1"
if not exist "!target_path!\" (
    echo ERROR: path not exist - !target_path!
    exit /b 1
)

echo scanning: !target_path!
echo =====================================


set "temp_file=%temp%\out_dirs_%random%.tmp"


(for /f "delims=" %%d in ('dir /ad /b /s "!target_path!\*.out" 2^>nul') do (
    set "dir_path=%%d"
    set "depth=0"
    for %%p in ("!dir_path:\=" "!") do set /a "depth+=1"
    echo !depth!:%%d
)) > "%temp_file%"


for %%f in ("%temp_file%") do if %%~zf equ 0 (
    echo found 0 folder with suffix .out
    del "%temp_file%" >nul 2>&1
    pause
    exit /b
)


set counter=0
for /f "tokens=1,* delims=:" %%i in ('sort /r "%temp_file%"') do (
    set /a counter+=1
    set "original_path=%%j"
    set "processed_path=%%j"
    

    if "!processed_path:~-4!"==".out" (
        set "processed_path=!processed_path:~0,-4!"
    )
    
    echo [folder !counter!]
    echo depth: %%i
    echo processing: !original_path!
    python3 tsspack.py repack "!original_path!" "!processed_path!"
    echo -------------------------------------
)

del "%temp_file%" >nul 2>&1
echo =====================================
echo finished
echo found !counter! folders to repack
echo try repack new.sp file...
python3 tsspack.py repacksp "!target_path!"
pause
endlocal
