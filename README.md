+---------------------------------------------------------------------------------------+
|                                    T R U F F L E _ D O G                              |
|                         XML-Personensuche (GUI · Tkinter · CSV-Export)                |
+---------------------------------------------------------------------------------------+

README.md — Schön formatiert im Monospace/ASCII-Stil. Einfach kopieren & als README.md speichern.
Dieses Tool durchsucht XML-Bestände nach Personen anhand von Geburtsdatum, Name oder beidem.
Während der Suche läuft unten ein animierter Suchhund; oben rechts wird ein Logo angezeigt.

========================================================================================
  I N H A L T
----------------------------------------------------------------------------------------
  1) Highlights
  2) Schnellstart
  3) Bedienung (Step by Step)
  4) Was wird durchsucht? (Schema)
  5) XML-Namespace & Minimalbeispiel
  6) Screens & Branding (Bilder)
  7) Troubleshooting (Git & App)
  8) Leistung & Grenzen
  9) Packen als EXE (Windows)
 10) Git-Kurzrezepte
 11) Roadmap
 12) Lizenz / Autor
========================================================================================


1) H I G H L I G H T S
----------------------------------------------------------------------------------------
- Suche nach:  (A) Geburtsdatum  (B) Name  (C) Beides (UND)
- Rekursives Durchsuchen eines Verzeichnisses nach *.xml
- Namespace-sicher: http://www.unisys.com/polis/staatsarchiv/geschaeftsliste
- Hintergrund-Thread → UI bleibt responsiv
- Fortschrittsbalken, Abbrechen, CSV-Export
- Doppelklick auf Ergebnis → Datei mit System-App öffnen
- Branding: Logo oben rechts  ·  Suchhund (Animation) unten während der Suche

Systemanforderungen:
- Python 3.9+ (empfohlen 3.10+)
- Tkinter (bei Standard-Python bereits dabei)
- Optional: tkcalendar (schöner Date-Picker → Datum sicher im Format YYYY-MM-DD)


2) S C H N E L L S T A R T
----------------------------------------------------------------------------------------
Windows (CMD oder Git Bash):

  python -m venv .venv
  .venv\Scripts\activate
  python -m pip install tkcalendar   (optional, aber empfohlen)
  python Truffledog_1.py

Tipp: Starte aus einer Konsole, um Debug-Ausgaben live zu sehen.


3) B E D I E N U N G   (S T E P   B Y   S T E P)
----------------------------------------------------------------------------------------
+-------------------------------------------------------------------------------------+
| [Suchart]  (o Geburtsdatum   o Name   o Beides)                                     |
| [Geburtsdatum]  Kalender (falls tkcalendar) oder Tag/Monat/Jahr Combos              |
| [Name]  ____________________________________________________________                |
| [Verzeichnis wählen]  C:\...\Bingo\Bestand\                                        |
| [Löschen] [Suchen] [Abbrechen] [Exportieren CSV]          [▓▓▓▓▓▓░░░░] 73%         |
+-------------------------------------------------------------------------------------+

Ergebnisse (doppelklickbar):
  Name                | Geburtsdatum | Datei
  ------------------- | ------------ | -----------------------------------------------
  Hans Muster         | 1985-12-03   | C:\...\Akte-4711.xml
  ...

Exportieren → CSV mit allen Treffern (Name, Geburtsdatum, Datei).


4) W A S   W I R D   D U R C H S U C H T ?   ( S C H E M A )
----------------------------------------------------------------------------------------
Verzeichnis ──(rekursiv)──► *.xml
                                 │
                                 ├─ parse: //ns:Person/ns:Name
                                 └─ parse: //ns:Person/ns:Geburtsdatum  (YYYY-MM-DD)
                                        │
                                        ├─ Suchart: birth → exakter Datumsvergleich
                                        ├─ Suchart: name  → Teilstring (case-insensitive)
                                        └─ Suchart: both  → beides (UND)


5) X M L - N A M E S P A C E   &   M I N I M A L B E I S P I E L
----------------------------------------------------------------------------------------
Namespace:
  http://www.unisys.com/polis/staatsarchiv/geschaeftsliste

Minimalbeispiel:
  <?xml version="1.0" encoding="UTF-8"?>
  <Geschaeftsliste xmlns="http://www.unisys.com/polis/staatsarchiv/geschaeftsliste">
    <Personen>
      <Person>
        <Name>Hans Muster</Name>
        <Geburtsdatum>1985-12-03</Geburtsdatum>
      </Person>
    </Personen>
  </Geschaeftsliste>

Hinweis: Intern wird Datum als YYYY-MM-DD verglichen. Der Date-Picker (tkcalendar) setzt das korrekt.


6) S C R E E N S   &   B R A N D I N G   ( B I L D E R )
----------------------------------------------------------------------------------------
Erwartete Dateien (gleicher Ordner wie Skript ODER absolute Pfade):
  Logo:      Logo.png
  Suchhund:  Suchhund.png

Während der Suche läuft der Hund unten (Canvas). Oben rechts sitzt das Logo (automatisch skaliert).


7) T R O U B L E S H O O T I N G
----------------------------------------------------------------------------------------
A) Git: „detected dubious ownership … safe.directory“
   Ursache: Ordner gehört laut Windows-SID einem anderen User als dein Git-Prozess.
   Fix in Git Bash IM REPO:
     git config --global --add safe.directory "$(pwd -W)"

   Falls IDE weiter meckert, denselben Befehl im IDE-Terminal ausführen.
   Notfalls (weniger sicher):  git config --global --add safe.directory "*"

B) GitHub: „Repository not found“ / „403 … denied to lean-drops“
   1. Remote prüfen:
      git remote set-url origin https://github.com/stazhhab/Truffle_Dog.git
      git remote -v
   2. Gespeicherte falsche Credentials löschen:
      printf "protocol=https\nhost=github.com\n" | git credential-manager-core erase
      (ggf. Windows-Anmeldeinformationsverwaltung öffnen und GitHub-Eintrag entfernen)
   3. Beim nächsten Push:
      Username:  stazhhab
      Password:  dein Personal Access Token (PAT) (mit repo-Rechten)

C) „nothing added to commit“
   Vorher stagen:
     git add -A
     git commit -m "feat: initial commit"

D) CRLF-Warnung
   Unkritisch auf Windows. Optional:
     git config core.autocrlf true


8) L E I S T U N G   &   G R E N Z E N
----------------------------------------------------------------------------------------
+ Responsive durch Hintergrund-Thread; UI friert nicht ein
+ Robuste Fehlertoleranz (Parse-Fehler einzelner Dateien werden protokolliert)
- Nur XML (keine XLS/XLSX, keine PDFs, keine Kommentare/Shapes)
- Geburtsdatum muss als YYYY-MM-DD vorliegen


9) P A C K E N   A L S   E X E   ( W I N D O W S )
----------------------------------------------------------------------------------------
PyInstaller:
  python -m pip install pyinstaller
  pyinstaller --noconsole --onefile ^
    --add-data "Logo.png;." ^
    --add-data "Suchhund.png;." ^
    Truffledog_1.py

macOS/Linux: Bei --add-data ist das Trennzeichen ":" statt ";"


10) G I T - K U R Z R E Z E P T E   ( F Ü R   D I E S E S   R E P O )
----------------------------------------------------------------------------------------
Erstes Commit:
  printf ".idea/\n__pycache__/\n*.pyc\nnul\n" > .gitignore
  git add -A
  git commit -m "feat: initial commit (TruffleDog GUI + assets)"

Remote setzen & pushen (GitHub-Repo vorher anlegen):
  git remote add origin https://github.com/stazhhab/Truffle_Dog.git
  git branch -M main
  git push -u origin main

Später:
  git pull --rebase
  git push


11) R O A D M A P
----------------------------------------------------------------------------------------
[ ] (UI) Einzel-XML direkt auswählen (optional zur Verzeichnissuche)
[ ] (UX) Live-Filterzeile über der Ergebnisliste
[ ] (DX) Protokoll-CSV je Lauf (Start/Ende, Anzahl Dateien, Treffer)
[ ] (QA) Unit-Tests für Namespace/Parser


12) L I Z E N Z   /   A U T O R
----------------------------------------------------------------------------------------
Lizenz: TBD (Vorschlag: Apache-2.0 oder MIT)

Autor:
  GitHub:  @stazhhab
  E-Mail:  leandro.habegger@zh.ch

+---------------------------------------------------------------------------------------+
|                                         ENDE                                          |
+---------------------------------------------------------------------------------------+
