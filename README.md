# Kaffeekasse

Kaffeeliste - Ein Programm zum Verwalten der Kaffeekasse
© Christian Post 2019

--- Dateien: ---
 kaffeeliste.py 	Hauptprogramm
 coffee_data.dat 	Datei (python pickle-Format) mit den gespeicherten Daten (nicht löschen!)
 log.txt 		Textdatei in der alle (Fehler-)meldungen aufgezeichnet werden
Ordner:
 temp			Ordner für Dateien, die während der Ausführung erzeugt werden. 
			Kann gefahrlos gelöscht werden
 exported_csv 		Ordner für exportierte CSV-Dateien (Listen etc.) als Sicherungskopien
			Können sowohl vom Programm erzeugt, als auch teilweise eingelesen werden
 backup			Ordner für Sicherungen der Datei coffee_data.dat
			Das Programm sichert alle 14 Tage (standardmäßige Einstellung) die Daten als 
			data_backup_YYYYMMDD.dat
			Diese können mit der Funktion "Daten wiederherstellen" eingelesen werden.

--- Funktionen: ---
 Datei
 - Änderungen speichern		Speichert alle Daten in coffee_data.dat
 - Exportieren			Funktion zum Exportieren diverser Datensätze als CSV-Dateien
 - Einstellungen		Backup-Intervall: Zeitraum, nach dem ein neues Backup erstellt wird
				(standardmäßig 14 Tage)
				Preis pro Strich: Wie viel €-Cent ein Strich kostet
				Debug Mode: Wenn aktiviert, werden Änderungen nicht gespeichert.
 - Beenden			Schließt das Programm. Falls Änderungen vorgenommen werden, 
				wird gefragt ob man speichern möchte.
 Personal
 - Hinzufügen			Anlegen einer neuen Person für die Kaffeeliste
 - Liste bearbeiten		Ermöglicht das Ändern der Namen und das Archivieren von Personen
 - Archiv			Ermöglicht das Ändern der Namen und das Wiederherstellen von Personen
				im Archiv (diese tauchen nicht auf den Kaffeelisten auf, sind aber 
				noch gespeichert)
 - Statistiken			--- noch in Arbeit ---

 Geldein-/ausgang
 - Eintrag
 -- Mitarbeiter			Ermöglicht das Eintragen von Bezahlungen durch Mitarbeiter (bei 
				Auszahlungen muss ein negativer Geldbetrag eingetragen werden)
 -- Verbrauchsmaterial		Eintragen von Besorgungen (Kaffee, Milch, Filter, etc)
 -- Sonderkasse/Feierkasse	Geldbewegungen in oder aus der Sonder- oder Feierkasse
 - Bearbeiten 			--- noch in Arbeit ---
 - Übersicht			Übersicht über Geldeingänge der Mitarbeiter

 Striche
 - Eintrag			Erzeugt eine Tabelle, wo für alle aktiven Personen die Striche
				eingetragen werden können.
 - Aus Datei			List Striche aus CSV-Datei. Die Datei muss mindestens die Spalten "ID"
				(Mitarbeiter-ID) und "Striche" enthalten. Jeder Person wird beim 
				Erstellen eine ID zugeordnet. Diese kann in der exportierten Datei
				"Mitarbeiterliste" eingesehen werden.

 Drucken
 - Strichliste			Erzeugt eine HTML-Datei mit einer leeren Strichliste, die dann im Browser
				geöffnet wird. Diese kann danach ausgedruckt werden.
 - Kontostand			Erzeugt eine HTML-Datei mit einer Liste der offenen Beträge bzw. Überschüsse
				für alle aktiven Mitarbeiter.
 - Geldein-/ausgänge		Erzeugt eine HTML-Datei mit einer Liste aller Veränderungen in allen Kassen
 - Konfigurieren
 -- Strichliste			Einstellmöglichkeiten, welche aktiven Mitarbeiter auf der Strichliste zu sehen
				sind, sowie der Anzahl leerer Zeilen am Ende
 -- Kontostand			--- noch in Arbeit ---
