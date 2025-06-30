@echo off
echo ================================
echo CELLULAR NETWORK MANAGER BUILDER
echo ================================
echo.

REM Verifica NSIS installato
where makensis >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERRORE: NSIS non trovato!
    echo Scarica da: https://nsis.sourceforge.io/Download
    echo Installa NSIS e riprova
    pause
    exit /b 1
)

echo Compilazione installer...
makensis installer.nsi

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ INSTALLER CREATO CON SUCCESSO!
    echo File: CellularNetworkManager_Installer.exe
    echo.
    echo Questo file installa il programma su qualsiasi PC Windows
    echo Il cliente dovrà solo eseguire l'installer come amministratore
    echo.
) else (
    echo.
    echo ✗ ERRORE durante la compilazione
    echo Verifica i file e riprova
    echo.
)

pause
