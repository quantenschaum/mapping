# Karten Drucken

Es gibt mehrere Möglichkeiten, Karten zu drucken. Sie können die Rasterdaten direkt aus Ihrem Browser heraus drucken (schnell und einfach) oder Vektordaten aus QGIS drucken (bessere Qualität, aber aufwendiger).

![exported chart image](img/chartimage.webp)

## Drucken aus dem Browser

1. Öffnen Sie die Karte im Browser (funktioniert am besten in Chrome-basierten Browsern).
2. Klicken Sie auf die Schaltfläche Drucklayout irgendwo oben links und wählen Sie das gewünschte Zielpapierformat und die Ausrichtung.
3. Passen Sie den Zoom und die Position der Karte nach Ihren Wünschen an.
4. Drucken Sie nun das Diagramm aus (Strg+P). Im Druckdialog
     - wählen Sie das richtige Papierformat und die richtige Ausrichtung
     - Stellen Sie die Ränder auf keine oder null oder minimal
     - Das Diagramm sollte auf einer einzelnen Seite zentriert sein
5. Drucken!

!!! tip "Zoomstufe und Symbolgröße"
    Bei aktivem Drucklayout können Sie eine halbe Zoomstufe herauszoomen, um mehr Inhalt in die Karte einzupassen und den Text und die Symbole kleiner erscheinen zu lassen, ohne tatsächlich in eine andere Zoomstufe zu wechseln.
    
!!! hint "PDF drucken"
    Sie können in eine PDF-Datei drucken, anstatt direkt auf Papier zu drucken. Auf diese Weise können Sie die Karte speichern, um sie später erneut zu drucken. Sie können die Karte auch als A3-PDF drucken und dieses dann auf A4 verkleinert ausdrucken. So erhalten Sie einen Ausdruck mit höherer Auflösung, aber kleinerem Text und Symbolen.

    Das Drucken von PDFs ist im Allgemeinen zuverlässiger als das Drucken direkt aus Anwendungen. Oft lässt sich der Drucker besser steuern und es stehen mehr Optionen zur Verfügung. Wenn also das Drucken direkt aus dem Browser fehlschlägt, versuchen Sie, in eine PDF-Datei zu drucken, und drucken Sie dann die PDF-Datei aus Ihrem PDF-Viewer.

!!! hint "Papier und Tinte"
    Es ist sehr zum empfehlen einen Laser-Drucker zu verwenden, denn der Toner ist wasserfest. Die Tinte aus Tintenstrahldruckern ist dies in der Regel nicht und verläuft bei Wasserkontakt, was den Ausdsruck unbrauchbar macht. Es gibt auch wasserfestes Papier aus behandelter Baumwolle oder Kunststoff, was für Laser-Drucker geeignet ist, so erhält man einen wasserbeständigen Ausdruck.

### Bild-Export

Mit der Pfeil-Schaltfläche im Druck-Widget oben links können Sie die aktuell angezeigte Karte als Bilddatei exportieren. Sie können die Größe des Browserfensters vor dem Export auf die gewünschte Größe anpassen oder ein vordefiniertes Drucklayout auswählen.

Dies ist nützlich, um Screenshots der Karte wie oben ohne die Steuerelemente, aber mit dem Seekartenrand zu erstellen.
 
## Drucken aus QGIS

Sie können mit QGIS eine Karte [wie diese](img/paperchart.pdf) erstellen.

Sie können Ihre eigenen benutzerdefinierten Karten mit dem klassischen Seekartenrand wie folgt drucken.

1. Installieren Sie [QGIS](https://qgis.org/) auf Ihrem Computer.
2. Laden Sie die [Rohdaten](index.md) herunter, das alle notwendigen Dateien enthält.
3. Entpacken Sie das Datenpaket.
4. Öffnen Sie `bsh.qgs` mit QGIS.
5. Wählen Sie `Projekt > Layout Manager`.
6. Doppelklicken Sie auf das Layout `paperchart` und der Layout-Editor wird geöffnet.
7. Passen Sie das Layout nach Ihren Wünschen an, wählen Sie den Teil der Karte aus, den Sie drucken möchten (verwenden Sie das Werkzeug zum Verschieben des Karteninhalts (C)).
8. Exportieren Sie die Karte als PDF.
9. Drucken Sie das PDF aus (direktes Drucken aus QGIS kann funktionieren, aber PDFs zu drucken, ist normalerweise zuverlässiger und Sie können es speichern, um es erneut zu drucken).

## Große Formate

Es ist möglich die Karten auf Formaten größer als A4 auszudrucken. Da man in der Regel jedoch nur einen A4-Drucker besitzt, druckt man die Karte verteilt auf mehrere A4-Blätter aus und klebt diesen anschließed zu einer Karte beliebiger Größe zusammen. Dabei geht man wie folgt vor.

1. zu druckende Karte als PDF mit einer Seite in der gewünschten Größe erstellen, dabei auf die Auflösung und Größe von Schift und Symbolen im Zielformat achten, für beste Qualität QGIS verwenden oder ein entprechend großes Format wählen (ist dann ggf. nicht vollständig auf dem Bildschirm sichtbar, mit Strg-Minus kann man rauszoomen, Strg-0 setzt zurück auf 100%) und in PDF drucken, dazu die Ränder und Papierformat entsprechend einstellen.
2. dieses PDF auf mehrere A4-Blätter verteilen, entweder kann der verwendte PDF-Viewer dies bereits oder man verwendet [dieses Script](https://github.com/quantenschaum/mapping/blob/master/scripts/poster.py) (benötigt Linux, Python, pdfposter, LaTeX). Mit der Option `-p` kann man die gewünsche Anzahl Seiten angeben, z.B. `-p 4x2` verteilt die Karte auf 4x2=8 Blätter, was ungefähr A1 enspricht (etwas kleiner wegen überlappender Klebefugen)
3. die Seiten ausdrucken, dabei die Autoskalierung des Druckers abschalten
4. den je unteren und rechten Rand abschneiden, dazu die Schnittmarken verwenden
5. Karte zusammenkleben

!!! example "Beispielkarte"
    Das folgende Beispiel zeigt die Elbmündung, einaml aus dem Browser als A1-PDF erzeugt und auf 4x2 A4-Blätter verteilt und einmal aus QGIS erzeugt.    
    
    - Browser (Rastergrafik)
        - [Beispielkarte A1, eine Seite](img/FreeNauticalChart.pdf)
        - [Beispielkarte A1, 4x2 A4](img/FreeNauticalChart.4x2.pdf)
    - QGIS (Vektorgrafik, hohe Qualität)
        - [Beispielkarte A1, eine Seite](img/paperchart.A1.pdf)
        - [Beispielkarte A1, 4x2 A4](img/paperchart.4x2.pdf)
