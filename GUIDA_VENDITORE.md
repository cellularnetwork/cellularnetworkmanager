# GUIDA CREAZIONE INSTALLER

## Preparazione (fai una volta)

1. **Scarica NSIS**: https://nsis.sourceforge.io/Download
2. **Installa NSIS** su Windows (serve makensis.exe)
3. **Trova un'icona** (.ico) e rinominala "icon.ico"

## Creazione Installer

1. **Copia icon.ico** nella cartella installer_package/
2. **Esegui**: `build_installer.bat`
3. **Ottieni**: `CellularNetworkManager_Installer.exe`

## Vendita Cliente

### Prezzo Consigliato: €3.500
- Software completo
- Installer professionale  
- Licenza d'uso perpetua
- Supporto 12 mesi

### Cosa ottiene il cliente:
✅ File installer .exe professionale
✅ Installazione automatica su Windows
✅ Icone desktop e menu start
✅ Database salvato in cartella utente sicura
✅ Backup automatico locale
✅ Disinstaller completo
✅ Guida utente completa

### Il cliente deve solo:
1. Eseguire installer come amministratore
2. Seguire procedura guidata
3. Usare il programma (icona desktop)

### Dati sicuri:
- Database in C:\Users\[username]\CellularNetworkData
- Backup automatici nella sottocartella backups/
- Dati preservati anche se disinstalla programma

## Aggiornamenti Futuri

Per nuove versioni:
1. Modifica numero versione in installer.nsi
2. Sostituisci file app/ con nuova versione
3. Ricompila installer
4. Cliente sostituisce installer (dati preservati)

---

**NOTA**: Una volta venduto, il cliente è completamente autonomo.
Tu non devi gestire niente!
