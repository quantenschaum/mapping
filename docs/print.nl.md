# Kaarten afdrukken

Er zijn meerdere manieren om een kaart af te drukken. Je kunt de rastergegevens direct vanuit je browser afdrukken (snel en eenvoudig) of vectorgegevens vanuit QGIS afdrukken (betere kwaliteit maar ingewikkelder).

![exported chart image](img/chartimage.webp)

## Afdrukken vanuit browser

1. Open de kaart in de browser (werkt het beste in browsers op basis van Chrome).
2. Klik op de printlayoutknop ergens linksboven en selecteer het gewenste papierformaat en de gewenste afdrukstand.
3. Pas de zoom en positie van de kaart naar wens aan.
4. Druk nu de kaart af (ctrl+p). In de afdrukdialoog
     - selecteer het juiste papierformaat en de juiste afdrukstand
     - stel marges in op geen, nul of minimaal
     - de grafiek moet gecentreerd zijn op een enkele pagina
5. Afdrukken!

!!! tip "zoomniveau en symboolgrootte"
    Met een actieve afdruklayout kun je een halve zoomstap uitzoomen om wat meer inhoud van de kaart te passen en de tekst en symbolen kleiner te laten lijken zonder daadwerkelijk naar een ander zoomniveau over te schakelen.
    
!!! hint "afdrukken naar PDF"
    Je kunt afdrukken naar PDF in plaats van direct op papier. Zo kun je de kaart opslaan en later opnieuw afdrukken. Je kunt de kaart ook afdrukken naar een A3 PDF, die kan worden verkleind naar A4. Dit zorgt voor een afdruk met een hogere resolutie, maar met kleinere tekst en symbolen.

    Het afdrukken van PDF's is over het algemeen betrouwbaarder dan het rechtstreeks afdrukken vanuit apps. Vaak is er betere controle over de printer en zijn er meer opties beschikbaar. Dus, als rechtstreeks afdrukken vanuit de browser mislukt, probeer dan af te drukken naar PDF en druk vervolgens de PDF af vanuit je PDF-viewer.

### Afbeelding exporteren

Met de onderste van de twee knoppen in de printwidget linksboven kun je de momenteel getoonde kaart exporteren als een afbeeldingsbestand. Je kunt de grootte van het browservenster aanpassen aan de gewenste grootte voordat je gaat exporteren, of je kunt een printlayout selecteren.

Dit is handig voor het maken van schermafbeeldingen van de kaart zonder de bedieningselementen, maar met de lat/lon randen.

## Afdrukken vanuit QGIS

Je kunt QGIS gebruiken om een kaart te maken [zoals deze](paperchart.pdf).

Je kunt als volgt je eigen aangepaste kaarten afdrukken met de klassieke lat/lon zebrarand.

1. Installeer [QGIS](https://qgis.org/) op uw computer.
2. Download het [datapakket](qmap-data.zip){:download} dat alle benodigde bestanden bevat.
3. Pak het gegevenspakket uit.
4. Open `rws.qgs` met QGIS.
5. Selecteer `Project > Layout Manager`.
6. Dubbelklik op de `paperchart` layout en de layout editor wordt geopend.
7. Pas de lay-out naar wens aan, selecteer het deel van de kaart dat je wilt afdrukken (gebruik het verplaatsgereedschap (C)).
8. Exporteer als PDF.
9. Druk de PDF af (rechtstreeks afdrukken vanuit QGIS kan werken, maar PDF afdrukken is meestal betrouwbaarder en je kunt het opslaan om het opnieuw af te drukken).
