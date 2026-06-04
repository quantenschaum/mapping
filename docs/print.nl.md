# Kaarten afdrukken

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

!!! hint "Papier en Inkt"
    Het wordt sterk aangeraden om een laserprinter te gebruiken, omdat toner watervast is. Inkt van inkjetprinters is doorgaans niet watervast en kan bij contact met water uitlopen, waardoor de afdruk onbruikbaar wordt. Er bestaat ook watervast papier van behandeld katoen of kunststof dat geschikt is voor laserprinters; daarmee krijgt u een waterbestendige afdruk.

### Afbeelding exporteren

Met de pijlknop in de printwidget linksboven kun je de momenteel getoonde kaart exporteren als een afbeeldingsbestand. Je kunt de grootte van het browservenster aanpassen aan de gewenste grootte voordat je gaat exporteren, of je kunt een printlayout selecteren.

Dit is handig voor het maken van schermafbeeldingen van de kaart zonder de bedieningselementen, maar met de lat/lon randen.

## Grote formaten

Het is mogelijk kaarten af te drukken op formaten groter dan A4. Omdat men meestal slechts een A4-printer heeft, print men de kaart verspreid over meerdere A4-bladen en plakt men deze daarna samen tot een kaart van de gewenste grootte. Ga als volgt te werk.

1. Maak van de te printen kaart een PDF met één pagina in het gewenste formaat. Let daarbij op de resolutie en de grootte van letters en symbolen in het eindformaat. Voor de beste kwaliteit kies een overeenkomstig groot formaat (dat mogelijk niet volledig op het scherm zichtbaar is; met Ctrl-Minus kun je uitzoomen, Ctrl-0 zet terug naar 100%) en exporteer naar PDF. Stel de marges en het papierformaat dienovereenkomstig in.
2. Verdeel deze PDF over meerdere A4-bladen. Sommige PDF-viewers kunnen dit al doen; anders kun je [dit script](https://github.com/quantenschaum/mapping/blob/master/scripts/poster.py) gebruiken. Met de optie `-t` kun je het gewenste aantal pagina's opgeven, bijv. `-t 4x2` verdeelt de kaart over 4x2=8 bladen, wat ongeveer overeenkomt met A1 (iets kleiner door overlappende lijmvoegen).
3. Print de pagina's uit en zet de automatische schaling van de printer uit.
4. Snijd telkens de onder- en rechterrand weg; gebruik daarvoor de snijtekens.
5. Plak de vellen aan elkaar tot één grote kaart.

!!! example "Voorbeeldkaart"
    Het volgende voorbeeld toont de Elbemonding als één A1-PDF en verdeeld over 2x4 A4-vellen, geprint naar PDF vanuit de browser.

    - [Voorbeeldkaart A1, enkele pagina](img/FreeNauticalChart.pdf)
    - [Voorbeeldkaart A1, 2x4 A4](img/FreeNauticalChart.2x4.pdf)

!!! tip
    Afdrukken met Firefox kan leiden tot een zeer slechte kwaliteit; gebruik daarom bij voorkeur een browser op basis van Chrome.
