
; Cellular Network Manager Installer
; Installer professionale per Windows

!define APPNAME "Cellular Network Manager"
!define COMPANYNAME "Cellular Network Solutions"
!define DESCRIPTION "Sistema di gestione multi-negozio"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "mailto:supporto@cellular-network.it"
!define UPDATEURL "http://www.cellular-network-manager.it"
!define ABOUTURL "http://www.cellular-network-manager.it"

!define INSTALLSIZE 50000  ; Stima KB

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\${APPNAME}"

; rtf or txt file - remember if it is txt, it must be in the DOS text format (\r\n)
LicenseData "license.txt"
Name "${APPNAME}"
Icon "icon.ico"
outFile "CellularNetworkManager_Installer.exe"

!include LogicLib.nsh

page license
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Amministratore richiesto!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    # Crea directory installazione
    setOutPath $INSTDIR
    
    # Copia file applicazione
    file /r "app\*.*"
    
    # Crea collegamento desktop
    createShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\launcher.py" "" "$INSTDIR\icon.ico"
    
    # Crea collegamento menu start
    createDirectory "$SMPROGRAMS\${APPNAME}"
    createShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\launcher.py" "" "$INSTDIR\icon.ico"
    createShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    # Crea cartella dati utente
    setShellVarContext current
    createDirectory "$PROFILE\CellularNetworkData"
    createDirectory "$PROFILE\CellularNetworkData\backups"
    
    # Registry per uninstaller
    setShellVarContext all
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    # Crea uninstaller
    writeUninstaller "$INSTDIR\uninstall.exe"
    
    # Messaggio finale
    messageBox MB_OK "Installazione completata!$\r$\nTrovi il programma sul Desktop e nel Menu Start$\r$\nI dati vengono salvati in: $PROFILE\CellularNetworkData"
sectionEnd

section "uninstall"
    # Rimuovi file
    rmDir /r "$INSTDIR"
    
    # Rimuovi collegamenti
    delete "$DESKTOP\${APPNAME}.lnk"
    rmDir /r "$SMPROGRAMS\${APPNAME}"
    
    # Rimuovi registry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    
    # Chiedi se rimuovere dati
    messageBox MB_YESNO "Vuoi rimuovere anche i dati (clienti, vendite, etc)?$\r$\nATTENZIONE: Questa operazione è irreversibile!" IDYES remove_data IDNO keep_data
    
    remove_data:
        rmDir /r "$PROFILE\CellularNetworkData"
        messageBox MB_OK "Disinstallazione completa"
        goto done
    
    keep_data:
        messageBox MB_OK "Programma rimosso, dati conservati in:$\r$\n$PROFILE\CellularNetworkData"
    
    done:
sectionEnd
