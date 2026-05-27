@echo off
title Habilitar Puertos en Windows Firewall - Vantti POS
color 0A

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ======================================================================
    echo           CONFIGURANDO WINDOWS FIREWALL PARA VANTTI POS
    echo ======================================================================
    echo.
    echo [!] Habilitando puerto 8080 para Flet Web...
    powershell -Command "New-NetFirewallRule -DisplayName 'Vantti POS Flet Web' -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow -Force" >nul 2>&1
    
    echo [!] Habilitando puerto 8000 para Django Backend...
    powershell -Command "New-NetFirewallRule -DisplayName 'Vantti POS Django Backend' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Force" >nul 2>&1

    echo [!] Habilitando puerto 8443 para Escaner HTTPS (camara)...
    powershell -Command "New-NetFirewallRule -DisplayName 'Vantti POS HTTPS Scanner' -Direction Inbound -LocalPort 8443 -Protocol TCP -Action Allow -Force" >nul 2>&1
    
    echo.
    echo ======================================================================
    echo  [OK] CONFIGURACION COMPLETADA CON EXITO!
    echo ======================================================================
    echo  Puerto 8080 (Flet), 8000 (Django) y 8443 (Escaner HTTPS) abiertos.
    echo  Ahora puedes conectar tu telefono celular usando la IP local.
    echo ======================================================================
    echo.
    pause
    exit
) else (
    echo ======================================================================
    echo  [ERROR] SE REQUIEREN PRIVILEGIOS DE ADMINISTRADOR
    echo ======================================================================
    echo.
    echo  Por favor, haz click derecho sobre este archivo y selecciona:
    echo  'Ejecutar como administrador'
    echo.
    echo ======================================================================
    echo.
    pause
    exit
)
