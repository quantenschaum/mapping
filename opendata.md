# Seekartendaten und Open-Data-Recht, eine rechtliche Einschätzung

*Disclaimer: Ich bin kein Jurist. Das folgende ist eine Einschätzung auf Basis öffentlich
zugänglicher Rechtsquellen, keine Rechtsberatung.*

---

## Worum geht es konkret?

Das BSH stellt Seekartendaten über den WMS-Dienst im GeoSeaPortal kostenlos unter der
GeoNutzV bereit, soweit korrekt. Gleichzeitig lizenziert es strukturierte Seekartendaten
kostenpflichtig an private Kartenverlage und hält bestimmte Datenschichten im öffentlichen
Dienst zurück, konkret Einzeltiefenmessungen (Spot Soundings).

Der Interessante Punkt dabei: Wir reden hier nicht über fertige Seekarten als kartografische
Produkte, sondern über die zugrundeliegenden **S-57-Vektordaten**, strukturierte Geodaten
mit Objektgeometrien und Attributen (Tiefen, Seezeichen, Fahrwasserachsen), aus denen Karten
erst erstellt werden. Die grafische Aufbereitung ist eine separate Leistung.

---

## Der Vergleich mit basemap.de / topografischen Karten

Topografische Kartendaten werden auf https://basemap.de frei bereitgestellt, ein hervorragender Service, vorbildlich. Diese Karten musste man vor einigen Jahren kaufen, jetzt gibt es sie kostenlos und top aktuell.

Das BKG (Bundesamt für Kartographie und Geodäsie) macht denselben Unterschied, und löst
ihn konsequent:

**Ebene 1, Rohdaten/Vektordaten (ATKIS Basis-DLM):** Straßen, Gewässer, Gebäude,
Vegetation als strukturierte Vektordaten. Diese stehen unter GeoNutzV bzw. CC BY 4.0 und
sind über das Geodatenzentrum des BKG kostenlos abrufbar.

**Ebene 2, Kartografisches Produkt (basemap.de):** Die daraus erzeugte fertige Webkarte
mit Darstellungsregeln, Generalisierung und redaktionellen Entscheidungen. Diese steht zwar
ebenfalls unter CC BY 4.0, ist aber ein eigenständiges Produkt mit eigenem Urheberrechtsschutz.

**Ebene 3, Topografische Papierkarte (TK25, TK50):** Separat lizenziertes kartografisches
Werk, nicht kostenlos.

Die Analogie zur Seekarte ist direkt: S-57-Vektordaten = ATKIS Basis-DLM. Fertige ENC =
basemap.de. Gedruckte Seekarte = TK25. Das BKG gibt Ebene 1 kostenlos heraus. Das BSH
tut das für die entsprechende maritime Ebene nicht vollständig, und genau hier liegt die
Spannungslage.

---

## Das rechtliche Schichtensystem

### INSPIRE-Richtlinie (2007/2/EG)

Definiert, was Geodaten sind. Seekartendaten fallen unter mehrere INSPIRE-Themen,
insbesondere *Höhe/Bathymetrie* (Anhang II) und *Gewässernetz* (Anhang I). Wichtig:
INSPIRE erfasst die zugrundeliegenden **Datensätze**, nicht fertige Kartenprodukte.
S-57-Vektordaten mit Tiefenwerten, Seezeichen und Fahrwasserachsen sind INSPIRE-Geodaten,
die fertige ENC als Navigationsinstrument ist ein Produkt, das darüber hinausgeht.

### PSI/Open-Data-Richtlinie (2019/1024/EU)

Legt fest, dass öffentliche Stellen ihre Daten grundsätzlich kostenlos und zur freien
Weiterverwendung bereitstellen müssen. Das klassische Kostendeckungsmodell, Lizenzgebühren
zur Refinanzierung der Datenerhebung, wurde damit weitgehend abgeräumt. Entscheidend ist
die **Grenzkostenregel**: Gebühren dürfen nur noch die Kosten der reinen Bereitstellung
decken, nicht die Erhebungskosten. Bei digitalen Daten sind Grenzkosten faktisch null.

### DVO-HVD, (EU) 2023/138, seit Juni 2024 verbindlich

Das ist die schärfste Stufe. Geodaten sind explizit als *hochwertige Datensätze* (HVD)
eingestuft. Für sie gilt:

- **Kostenlosigkeit**, ohne Ausnahme, auch keine Grenzkosten
- **Offene Lizenz**, CC BY 4.0 oder freier
- **Maschinenlesbare Bereitstellung** über standardisierte Schnittstellen

Entscheidend: Die Verordnung knüpft ausdrücklich nicht nur an öffentlich bereitgestellte
Daten an, sondern auch an Daten, die einer **ausschließlichen Nutzung durch Dritte**
zugänglich gemacht werden (§ 3 DNG). Eine Lizenzierung an Kartenverlage ist damit
ausdrücklich ein Bereitstellungstatbestand.

Die DVO-HVD schafft zwar keine neue Erhebungspflicht, aber das BSH erhebt die
Vermessungsdaten ohnehin aufgrund seiner gesetzlichen Pflicht nach dem **Seeaufgabengesetz**
(Sicherheit und Leichtigkeit des Seeverkehrs). Sobald diese Daten intern genutzt oder an
Verlage lizenziert werden, greifen die Open-Data-Pflichten.

---

## Das S-63-Argument greift nicht

Das S-63-Verschlüsselungssystem der IHO könnte als technisches Argument für eingeschränkte
Datenweitergabe herangezogen werden. Das ist kryptografisch jedoch nicht haltbar:

**Manipulationsschutz**, das eigentliche Sicherheitsziel, wird durch **digitale
Signaturen** erreicht, nicht durch Verschlüsselung. Signatur und Verschlüsselung sind
unabhängige kryptografische Mechanismen. Unverschlüsselte, aber signierte Daten sind
genauso manipulationssicher wie verschlüsselte. Die Verschlüsselung in S-63 dient
ausschließlich der kommerziellen Zugangskontrolle, und ist damit kein legitimes Argument
gegen Open-Data-Bereitstellung.

Zusätzlich: IHO-Standards sind technische Empfehlungen einer zwischenstaatlichen
Organisation, keine verbindlichen Rechtsnormen. Sie können EU-Recht nicht außer Kraft setzen.

---

## Europäischer Vergleich

Das BSH ist kein Einzelfall, das ist europäischer Normalzustand:

| Bereich | Verfügbarkeit | Beispiele |
|---|---|---|
| Binnenwasser Europa | Weitgehend frei | DE (WSV/ELWIS), NL, AT, PL, RO... |
| Küste/Offshore Europa | Fast überall kostenpflichtig | DE, FR, UK, NO, SE, DK... |
| Küste außerhalb EU | Teils frei | USA (NOAA), Neuseeland |
| Küste NL (Wattenmeer/Zeeland) | Frei | Ausnahme in Europa |

Der Unterschied zwischen freien Binnen-ENCs und kostenpflichtigen See-ENCs hat einen
konkreten Grund: Die EU-RIS-Richtlinie (2005/44/EG) hat für Binnenwasser offene
elektronische Karten **explizit vorgeschrieben**. Für Küsten-ENCs gibt es keine
vergleichbare sektorspezifische Richtlinie, die DVO-HVD ist der nächstmögliche Hebel,
aber ohne die politische Durchsetzungskraft einer dedizierten Richtlinie.

Die USA (NOAA) stellen sämtliche ENCs vollständig kostenlos als S-57-Dateien zum direkten
Download bereit, ohne Registrierung, ohne Verschlüsselung. Das zeigt, dass es technisch
und organisatorisch problemlos möglich ist.

---

## Was das BSH entlastet

Die Situation ist nicht allein dem BSH anzulasten. Der **Bundesrechnungshof** verlangt vom
BSH marktgerechte Einnahmen für seine Daten. Das steht in direktem Widerspruch zur
EU-Open-Data-Pflicht. Das BSH sitzt zwischen zwei widersprüchlichen staatlichen
Anforderungen, die der Gesetzgeber selbst erzeugt hat und bisher nicht aufgelöst hat.
Das ist kein Versagen des BSH, sondern ein strukturelles politisches Problem.

---

## Fazit

Die bisherige Praxis, S-57-Vektordaten mit Tiefenschichten zurückzuhalten und gleichzeitig
kostenpflichtig an Kartenverlage zu lizenzieren, ist mit der DVO-HVD und dem deutschen
Datennutzungsgesetz **schwer vereinbar**. Das gilt umso mehr, als das maritime Pendant zum
frei verfügbaren ATKIS Basis-DLM des BKG genau diese Vektordaten sind.

Eine abschließende rechtliche Klärung gäbe es nur durch die Europäische Kommission oder
ein Gericht. Bis dahin bleibt es ein institutionelles Übergangsdilemma, letztlich eine
politische Entscheidung auf Bundesregierungsebene. Adressen für weitere Recherche und
Öffentlichkeitsdruck wären netzpolitik.org sowie eine IFG-Anfrage über FragDenStaat.
