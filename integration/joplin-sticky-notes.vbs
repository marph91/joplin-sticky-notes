' copy "integration\joplin-sticky-notes.vbs" "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup"
' https://www.vbsedit.com/html/6f28899c-d653-4555-8a59-49640b0e32ea.asp
SET oShell = WScript.CreateObject("Wscript.Shell")
WScript.Sleep 10000  ' try to wait until joplin is started
oShell.run "pythonw -m joplin_sticky_notes"
