; This script is perhaps one of the simplest NSIs you can make. All of the
; optional settings are left to their default settings. The installer simply 
; prompts the user asking them where to install, and drops a copy of example1.nsi
; there. 

  !include "FileAssociation.nsh"

  !define MUI_PRODUCT "GodiRec"
  
;--------------------------------
; Branding Text

BrandingText "${MUI_PRODUCT}"

; The name of the installer
Name "${MUI_PRODUCT}"

; The file to write
OutFile "${MUI_PRODUCT}_Installer.exe"

; The default installation directory
InstallDir "$PROGRAMFILES\${MUI_PRODUCT}"

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${MUI_PRODUCT}" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

;UninstPage uninstConfirm
UninstPage components
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "${MUI_PRODUCT}.exe (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put file there
  File /r dist\*
  
  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\${MUI_PRODUCT}" "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT}" "DisplayName" "${MUI_PRODUCT}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu"

  CreateDirectory "$SMPROGRAMS\${MUI_PRODUCT}"
  CreateShortcut "$SMPROGRAMS\${MUI_PRODUCT}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\${MUI_PRODUCT}\${MUI_PRODUCT}.lnk" "$INSTDIR\${MUI_PRODUCT}.exe" "" "$INSTDIR\${MUI_PRODUCT}.exe" 0
  
SectionEnd

Section "Desktop Shortcut"

;create desktop shortcut
  CreateShortCut "$DESKTOP\${MUI_PRODUCT}.lnk" "$INSTDIR\${MUI_PRODUCT}.exe" ""
  
SectionEnd

Section "FileAssociation *.gdr"

;create FileAssociation
  ${registerExtension} "$INSTDIR\${MUI_PRODUCT}.exe" ".gdr" "GodiRec Project"
  
SectionEnd

;--------------------------------

; Uninstaller

Section "un.GodiRec"
    
  SectionIn RO
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT}"
  DeleteRegKey HKLM SOFTWARE\${MUI_PRODUCT}

  ; Remove files and uninstaller
  RMDir  /r $INSTDIR

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\${MUI_PRODUCT}\*.*"

  Delete "$DESKTOP\${MUI_PRODUCT}.lnk"
  ; Remove directories used
  RMDir "$SMPROGRAMS\${MUI_PRODUCT}"
  RMDir "$INSTDIR"

SectionEnd

; is unselected
Section /o "un.User Data (Settings)"

  ; Remove files and uninstaller
  RMDir  /r "$APPDATA\${MUI_PRODUCT}"

  ; Remove settings registry keys
  DeleteRegKey HKCU "Software\EFG Aachen\${MUI_PRODUCT}"

SectionEnd

Section "un.Delete File Association *.gdr"

  ; Remove FileAssociation
    ${unregisterExtension} ".gdr" "GodiRec Project"

SectionEnd