# Karten Drucken

Es gibt mehrere Möglichkeiten, Karten zu drucken. Sie können die Rasterdaten direkt aus Ihrem Browser heraus drucken (schnell und einfach) oder Vektordaten aus QGIS drucken (bessere Qualität, aber komplizierter).

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
    
!!! hint "in PDF drucken"
    Sie können in eine PDF-Datei drucken, anstatt direkt auf Papier zu drucken. Auf diese Weise können Sie die Karte speichern, um sie später erneut zu drucken. Sie können die Karte auch als A3-PDF drucken und dieses dann auf A4 verkleinert ausdrucken. So erhalten Sie einen Ausdruck mit höherer Auflösung, aber kleinerem Text und Symbolen.

    Das Drucken von PDFs ist im Allgemeinen zuverlässiger als das Drucken direkt aus Anwendungen. Oft lässt sich der Drucker besser steuern und es stehen mehr Optionen zur Verfügung. Wenn also das Drucken direkt aus dem Browser fehlschlägt, versuchen Sie, in eine PDF-Datei zu drucken, und drucken Sie dann die PDF-Datei aus Ihrem PDF-Viewer.

### Bild-Export

Mit der unteren der beiden Schaltflächen im Druck-Widget oben links können Sie die aktuell angezeigte Karte als Bilddatei exportieren. Sie können die Größe des Browserfensters vor dem Export auf die gewünschte Größe anpassen oder ein Drucklayout auswählen.

Dies ist nützlich, um Screenshots der Karte ohne die Steuerelemente, aber mit dem Seekartenrand zu erstellen.

![exported chart image](print/img-export.webp)
 
## Drucken aus QGIS

Sie können mit QGIS eine Karte [wie diese](print/Juist.pdf) erstellen.

![printed chart](print/chart.webp)

Sie können Ihre eigenen benutzerdefinierten Karten mit dem klassischen Seekartenrand wie folgt drucken.

1. Installieren Sie [QGIS](https://qgis.org/) auf Ihrem Computer.
2. Laden Sie das [Datenpaket](qmap-data.zip){:download} herunter, das alle notwendigen Dateien enthält.
3. Entpacken Sie das Datenpaket.
4. Öffnen Sie `bsh.qgs` mit QGIS.
5. Wählen Sie `Projekt > Layout Manager`.
6. Doppelklicken Sie auf das Layout `paperchart` und der Layout-Editor wird geöffnet.
   ![Layout-Editor](print/layout.webp)
7. Passen Sie das Layout nach Ihren Wünschen an, wählen Sie den Teil der Karte aus, den Sie drucken möchten (verwenden Sie das Werkzeug zum Verschieben des Karteninhalts (C)).
8. Exportieren Sie die Karte als PDF.
9. Drucken Sie das PDF aus (direktes Drucken aus QGIS kann funktionieren, aber PDFs zu drucken, ist normalerweise zuverlässiger und Sie können es speichern, um es erneut zu drucken).
