@echo off
title Editeur cKc
cd /d "%~dp0"

REM ============================================================
REM  Lanceur de l'editeur cKc (Streamlit) - version Python simple
REM  A placer dans le MEME dossier que app_procedures.py
REM  Double-cliquer sur ce fichier pour lancer l'application.
REM ============================================================

REM --- Trouve la commande Python disponible ---
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (
  where py >nul 2>nul && set "PY=py"
)

if not defined PY (
  echo.
  echo   Python est introuvable.
  echo   Installe-le depuis https://www.python.org en cochant
  echo   "Add python.exe to PATH", puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

REM --- Evite la question d'email au tout premier lancement de Streamlit ---
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >>"%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

REM --- Installe les composants la premiere fois si besoin (necessite internet) ---
%PY% -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo Premiere utilisation : installation des composants, merci de patienter...
  %PY% -m pip install streamlit pandas
)

REM --- Lance l'application (le navigateur s'ouvre tout seul) ---
%PY% -m streamlit run app_procedures.py

REM Garde la fenetre ouverte si un message s'affiche
echo.
pause
