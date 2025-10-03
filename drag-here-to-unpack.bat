
@echo off
setlocal enabledelayedexpansion


if "%~1"=="" (
    echo Usage: %~nx0 [the folder path where original.sp is]
    echo e.g.: %~nx0 "C:\folder_contains_original.sp_file"
    echo or just drag the folder to this batch file
    pause
    exit /b 1
)

set "root_dir=%~1"

echo try unpack original.sp file...
python3 tsspack.py unpacksp "%root_dir%"



set counter=0
for /r "%root_dir%" %%f in (*) do (
    set /a counter+=1
    set "original_path=%%f"
    set "new_path=%%f.out"
    echo processing: !original_path!
    python3 tsspack.py unpack "!original_path!" "!new_path!"
)

echo finished
echo found !counter! files to unpack
pause
endlocal
