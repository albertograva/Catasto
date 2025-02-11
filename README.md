lo script crea un unico file .gpkg con 2 layer uno con le particelle e uno con i fogli. Deve essere lanciato sulla cartella della Regione di interesse scaricata dal sito https://geodati.gov.it/geoportale/visualizzazione-metadati/scheda-metadati/?uuid=age:S_0000_ITALIA 

va lanciato dalla console python di QGIS con il comando:
exec(open('/percorso/catasto_regione.py').read())

lo script è impostato in modo da dare al gpkg in uscita il nome della cartella radice (che se non modificato dopo il download sarebbe quello della regione di interesse)

lo script ha bisogno di tempo per agire vista la mole di dati che elabora

il file in uscita è potenzialmente molto pesante.

le azioni richieste all'utente sono: 
1) dezippare il la cartella scaricata (solo il primo livello)
2) inserire il percorso della cartella nello script quando richiesto
