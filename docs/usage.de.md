# Verwendung

Wie verwendet man die Seekarte?

## Im Browser

Man kann die Karte im Browser wie jede andere Karte verwenden, um die Karte anzuzeigen und Törns zu planen.
Neben der Karte selbst gibt es einige zusätzliche Funktionen, die für die Navigation nützlich sind und im Folgenden erläutert werden.

## App-Modus

Die Seekarte kann als [PWA](https://en.wikipedia.org/wiki/Progressive_web_app) installiert werden.
Dazu wählt man "Installieren" oder "Zum Startbildschirm hinzufügen" aus dem Menü des Browsers.
Es funktioniert am besten mit Chrome-basierten Browsern.
Der App-Modus zeigt andere Symbole in der Symbolleiste als der Website-Modus, wie z.B. GPS-Position des Geräts, Nachtmodus mit dunklen Farben.

Zusätzlich werden im App-Modus die Kartenkacheln und Gezeitenvorhersagen, die man angesehen hat, in einem Cache gespeichert, um sie später offline verfügbar zu haben.
Ansonsten funktioniert es genauso wie die Karte im Browser, die App ist letztendlich nur ein Browser, nur im PWA-Modus.

## Drucken

Man kann Seekarten einfach direkt aus dem Browser drucken. Wie das geht, wird [hier](print.md) beschrieben.

## Gezeiten

Gezeitenhöhen und -strömungen können wie [hier](tides.md) beschrieben angezeigt werden. Sehr praktisch für die Törnplanung, dies direkt in der Seekarte verfügbar zu haben.

## Routen-Werkzeug

![Routen-Werkzeug](img/route-tool.webp)

Das Routen-Werkzeug (grüne Schaltfläche im Bild oben) ermöglicht es, Wegpunkte zu setzen und Kurs und Distanz zwischen ihnen abzulesen.

## Nachtmodus

Für die Verwendung bei Nacht gibt es einen Modus mit dunklen Farben. Man schaltet den Nachtmodus mit dem Mond-Symbol um.
Die Helligkeit wird invertiert, aber die Farben bleiben gleich.

## GPS-Tracking

Man kann auch das GPS des Geräts verwenden.
Tippt man auf das Boot-Symbol, wird die GPS-Position auf der Karte mit einem KüG-Vektor von 10 Minuten Länge angezeigt.
KüG und FüG werden in der linken unteren Ecke angezeigt.

# Karten-Werkzeuge

![Peilung](img/bearing.webp)

Dies ist eine besondere Funktion dieser Karte.
Sie kombiniert moderne Elektronik und eine digitale Seekarte mit klassischen Navigationsverfahren, wie sie auf einer Papierkarte durchgeführt wurden. Dies ermöglicht es, GPS- und klassische terrestrische Navigation zu kombinieren oder auf manuelle Navigation zurückzugreifen, falls das GPS ausfällt oder gestört wird.
Diese Art der halbautomatischen Navigation macht einen möglicherweise auch aufmerksamer dafür, was man tatsächlich tut und wo man sich wirklich befindet.
Beim Einhandsegeln oder sehr kleiner Crew ermöglichen die Karten-Werkzeuge, einen Schiffsort aus einigen Peilungen direkt auf der digitalen Seekarte mit wenigen Handgriffen zu plotten.
Man muss die Peilungen nicht aufschreiben, nach unten gehen, rechnen und mit Dreieck und Bleistift hantieren, wobei man möglicherweise seekrank wird.
Dies kann also die Sorgfalt, gute Seemannschaft und die Sicherheit verbessern.
Und schließlich ist es ein se gutes Werkzeug für Bildungszwecke. Man kann es verwenden, um sich selbst weiterzubilden oder um andere zu unterrichten sowie Material und Übungen vorzubereiten.

Die verfügbaren Werkzeuge sind (von links nach rechts)

- **Stift** - Symbolleiste öffnen/schließen
- **Radiergummi** - alle Zeichnungen löschen
- **Wegpunkt** - einen WP-Marker setzen
- **Peilung** - Peilungslinie zeichnen, rechtweisender und missweisender Wert wird angezeigt
- **Distanz** - Distanzkreis zeichnen
- **Peilung & Distanz** - Peilungslinie zeichnen und Distanzmarkierung setzen (Radar-Fix)
- **Verseglte Peilung** - Peilungslinie zeichnen, dann parallel entlang eines Kursvektors verschieben
- **Fix** - einen Schiffsort-Marker setzen
- **Koppeln** - Koppel-Linie mit Richtung und Distanz zeichnen
- **Stromaufgabe 1** - Stromdreieck, Koppel-Linie zeichnen, dann Stromvektor
- **Stromaufgabe 2** - Stromdreieck, Stromvektor zeichnen, dann Kurs über Grund, dann Fahrt durchs Wasser

## Elektronischer Kompass

Viele Smartphones und Tablets verfügen über eingebaute Sensoren für Magnetfeld und Beschleunigung. Diese können über die Sensors API des Browsers genutzt werden, sofern dies unterstützt wird. Der [AbsoluteOrientationSensor](https://developer.mozilla.org/en-US/docs/Web/API/AbsoluteOrientationSensor) erlaubt es, das Gerät als neigungskompensierten Magnetkompass zu verwenden. Man erhält eine genaue magnetische Peilung, auch wenn das Gerät nicht waagerecht gehalten wird. Durch Addition der Missweisung wird die magnetische Peilung automatisch in eine rechtweisende Peilung umgerechnet.

So kann das Smartphone als Kartenanzeige und als Handpeilkompass in einem Gerät dienen. Erkennt die App einen funktionierenden Orientierungssensor, erscheint ein zusätzliches Peilwerkzeug mit blauem Hintergrund. Tippt man das Symbol an und setzt einen Marker auf der Karte auf das gepeilte Objekt, wird die Peilungslinie automatisch entsprechend der Geräteorientierung gezeichnet. Tippt man dann irgendwo auf den Bildschirm, wird die Peilung eingefroren.

Da man das Gerät nicht waagrecht halten muss, kann man es leicht nach links oder rechts neigen und über eine seiner langen Kanten schauen und es auf das Objekt ausrichten. Man muss dazu nicht auf den Bildschirm schauen, sondern tippt einmal auf dem Bildschirm, wenn das Gerät ausgerichtet ist und ruhig gehalten wird.

!!! warning "Kompasskalibrierung"
    Für genaue Messwerte ist es unbedingt notwendig, **vor dem Peilen eine Kompasskalibrierung durchzuführen**. Dies lässt sich in der Regel in der Standard-Karten-App aufrufen, indem man den Positionsmarker antippt, oder man verwendet eine App wie [GPS Status](https://play.google.com/store/apps/details?id=com.eclipsim.gpsstatus2).
