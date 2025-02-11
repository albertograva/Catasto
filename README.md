lo script crea un unico file .gpkg con 2 layer uno con le particelle e uno con i fogli. Deve essere lanciato sulla cartella della Regione di interesse scaricata dal sito https://geodati.gov.it/geoportale/visualizzazione-metadati/scheda-metadati/?uuid=age:S_0000_ITALIA 

va lanciato dalla console python di QGIS con il comando:
exec(open('/percorso/catasto_regione.py').read())

lo script è impostato in modo da dare al gpkg in uscita il nome della cartella radice (che se non modificato dopo il download sarebbe quello della regione di interesse)
