# Getij

## Getijdentabellen en waterstand

Het Duitse BSH en de Nederlandse RWS stellen getijdendata beschikbaar via

- <https://gezeiten.bsh.de/>
- <https://wasserstand-nordsee.bsh.de/>
- <https://waterinfo.rws.nl/>

Deze zijn in de kaart geïntegreerd. Door op de blauwe markeringen te klikken ontvangt u in een pop-up de getijvoorspellingen voor de huidige en de volgende dag. Tenzij anders aangegeven is de referentiehoogte SKN/LAT.

![Getijdencijfers](img/tide-times.webp)

### Hoogte van het getij

De hoogte van het getij (HdG) is de hoogte ten opzichte van LAT, berekend met het [astronomische voorspellingsmodel](https://gezeiten.bsh.de). De daaropvolgende waarde K is een correctie die op de HdG moet worden toegepast en die de weersinvloeden bevat. Deze wordt eveneens door het BSH berekend en gepubliceerd in de [waterstandvoorspelling](https://wasserstand-nordsee.bsh.de).

!!! warning "Let op"
    Het BSH baseert zijn waterstandscorrectie op het gemiddelde hoog- respectievelijk laagwater; K daarentegen is relatief ten opzichte van de astronomische voorspelling en omvat uitsluitend de weersinvloeden.

### Getijcoëfficiënt

Analoog (maar toch anders) aan de Franse getijcoëfficiënt is de getijcoëfficiënt C ingevoerd. Deze wordt gedefinieerd als de verhouding van de actuele getijrijzing/-daling tot de gemiddelde springtijslag.

```
               | HW - NW |
C = 100 * ---------------------
          gemidd. springtijslag
```

Waar is dat nuttig voor? — U ziet onmiddellijk hoe de actuele rijzing/daling uitvalt ten opzichte van de gemiddelde springtijslag. Omdat de stroomsnelheid doorgaans rechtstreeks evenredig is met de rijzing/daling, kunt u C gebruiken om de in de getijdenstroomatlas vermelde spring-stroomsnelheid te schalen. Daarmee wordt de stroominterpolatie aanzienlijk eenvoudiger en sneller.

Deze wordt in elke rij berekend uit het hoogteverschil tussen deze en de voorgaande rij. Valt het gewenste tijdstip tussen twee rijen, dan leest u C af uit de onderste rij.

!!! example "Voorbeeld"
    Wilt u de stroomsnelheid op 28-02 om 1200 weten, dan leest u C bij het dichtstbijzijnde NW af als 78. Vermenigvuldig de in de getijdenstroomatlas afgelezen spring-stroomsnelheid eenvoudig met 0,78 om de geïnterpoleerde waarde te verkrijgen.

### Getijdencurven

![getijdencurve](img/tidecurve.webp)
Getijdencurven in ATT-stijl, berekend uit de door het BSH beschikbaar gestelde gegevens, kunt u [hier](index.md#gezeitenkurven) downloaden.

## Getijdenstroom

Het BSH stelt getijdenstroomgegevens beschikbaar voor de Noordzee, Het Kanaal en de Duitse Bocht (met hogere resolutie).

De weergave van deze gegevens in het [GeoSeaPortal](https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas) is helaas niet erg bruikbaar; men kan noch de dataset noch het getij-uur selecteren. De ruwe gegevens zijn echter beschikbaar onder [Noordzee](https://gdi.bsh.de/de/feed/Tidal-currents-North-Sea.xml)/[Kust](https://gdi.bsh.de/de/feed/Tidal-currents-German-coastal-waters-and-neighbouring-regions.xml).

Ik heb met [QGIS](https://qgis.org/) het getijdenstroomveld gerenderd en gegevens voor stroomsnelheid en -richting toegevoegd. U kunt het getij-uur selecteren; afhankelijk van het zoomniveau krijgt u een overzicht van de getijdenstroom en kunt u bij het juiste zoomniveau de waarden direct op de gewenste positie aflezen. Bij verder inzoomen wordt de kustdataset met hogere resolutie weergegeven.

![getijden](img/tides.webp)

De kaart ziet eruit zoals hierboven afgebeeld. Met de schuifregelaar kiest u het aantal uren vóór/na hoogwater Helgoland. De pijlen geven door hun grootte en kleur de gemiddelde stroomsnelheid en -richting aan. Het getal onder de pijl is de gemiddelde stroomrichting; de getallen boven de pijl zijn de stroomsnelheden in tienden knopen bij doodtij (nipptide, voor de punt) en bij springtij (na de punt).

![getijfiguren](img/figures.webp)

Wanneer de schuifregelaar op `fig` staat, worden de getijdenpijlen van alle uren tegelijk weergegeven om de getijdenstroomfiguur voor de betreffende locatie te tonen. De getallen staan voor het aantal uren vóór/na HW.
