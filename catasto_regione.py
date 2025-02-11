import os
import zipfile
import tempfile
import geopandas as gpd
from shapely.errors import GEOSException
import shutil

# Imposta la cartella radice
root_directory = "percorso cartella radice" ## ad esempio /home/alberto/Qsync/Lavoro/generale/Catasto/VENETO

# Nome del GPKG finale
final_gpkg = os.path.join(root_directory, f"{os.path.basename(root_directory)}.gpkg")

# Funzione per estrarre i file GML da ZIP annidati senza creare sottocartelle
def extract_gml_from_nested_zip(zip_path, temp_dir, provincia):
    extracted_files = {"ple": [], "map": []}

    print(f"🔍 Estrazione ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for file_name in zip_file.namelist():
            if file_name.endswith(".zip"):  # ZIP di terzo livello
                print(f"  📂 Trovato ZIP interno: {file_name}")
                with zip_file.open(file_name) as nested_zip_file:
                    with zipfile.ZipFile(nested_zip_file, 'r') as nested_zip:
                        for nested_file in nested_zip.namelist():
                            if nested_file.endswith("_ple.gml"):
                                extracted_path = nested_zip.extract(nested_file, temp_dir)
                                extracted_files["ple"].append((extracted_path, nested_file, provincia))
                            elif nested_file.endswith("_map.gml"):
                                extracted_path = nested_zip.extract(nested_file, temp_dir)
                                extracted_files["map"].append((extracted_path, nested_file, provincia))

    return extracted_files

# Funzione per unire i file GML e correggere geometrie corrotte, aggiungendo i nuovi campi
def merge_gml(files):
    if not files:
        return None
    gdfs = []
    for f, filename, provincia in files:
        try:
            print(f"  🔄 Unione file: {filename}")
            gdf = gpd.read_file(f)

            # Estrae il nome del comune (testo tra _ nel nome file)
            comune = filename.split("_")[1] if "_" in filename else filename

            # Corregge solo le geometrie non valide
            def fix_geometry(geom):
                if geom is None:
                    return None
                try:
                    return geom if geom.is_valid else geom.buffer(0)
                except GEOSException:
                    return None  # Scarta solo questa geometria

            gdf["geometry"] = gdf["geometry"].apply(fix_geometry)
            gdf = gdf[gdf["geometry"].notnull()]  # Rimuove solo le geometrie non recuperabili

            # Aggiunge i nuovi campi
            gdf["comune"] = comune
            gdf["provincia"] = provincia.upper()  # Ora tutto in maiuscolo

            gdfs.append(gdf)
        except Exception as e:
            print(f"❌ Errore nel file {f}: {e}")

    if gdfs:
        return gpd.pd.concat(gdfs, ignore_index=True)
    else:
        print("❌ Nessun dato valido dopo la fusione.")
        return None

# Liste per raccogliere i GPKG intermedi
gpkg_files = []

# Scansiona gli ZIP di secondo livello nella cartella radice
for zip_file_name in os.listdir(root_directory):
    if zip_file_name.endswith(".zip"):
        second_level_zip_path = os.path.join(root_directory, zip_file_name)

        # Prende solo le prime due lettere del nome del file ZIP (es. "VE" da "VE_F229.zip") e le mette in maiuscolo
        provincia = os.path.splitext(zip_file_name)[0][:2].upper()

        print(f"\n📂 Processando: {zip_file_name} (provincia: {provincia})")

        # Creazione di una cartella temporanea
        with tempfile.TemporaryDirectory() as temp_dir:
            all_gml_files = {"ple": [], "map": []}

            extracted_files = extract_gml_from_nested_zip(second_level_zip_path, temp_dir, provincia)
            all_gml_files["ple"].extend(extracted_files["ple"])
            all_gml_files["map"].extend(extracted_files["map"])

            # Verifica se ci sono file estratti
            if not all_gml_files["ple"] and not all_gml_files["map"]:
                print(f"❌ Nessun file .gml trovato in {zip_file_name}. Skip.")
                continue  # Passa al prossimo ZIP

            # Nome del file GPKG di output
            output_gpkg = os.path.join(root_directory, f"{provincia}.gpkg")
            gpkg_files.append(output_gpkg)  # Salva il nome del GPKG intermedio
            print(f"📁 GPKG di destinazione: {output_gpkg}")

            ple_layer = merge_gml(all_gml_files["ple"])
            map_layer = merge_gml(all_gml_files["map"])

            if ple_layer is not None:
                ple_layer.to_file(output_gpkg, layer="ple_layer", driver="GPKG")
                print(f"  ✔ Salvato layer 'ple_layer' in {output_gpkg}")
            else:
                print("  ❌ Nessun dato valido per 'ple_layer'.")

            if map_layer is not None:
                map_layer.to_file(output_gpkg, layer="map_layer", driver="GPKG")
                print(f"  ✔ Salvato layer 'map_layer' in {output_gpkg}")
            else:
                print("  ❌ Nessun dato valido per 'map_layer'.")

# Fusione finale dei GPKG in un unico GPKG
print("\n🔄 Unione di tutti i GPKG in uno solo...")

final_ple_layers = []
final_map_layers = []

for gpkg in gpkg_files:
    try:
        ple_layer = gpd.read_file(gpkg, layer="ple_layer")
        final_ple_layers.append(ple_layer)
    except Exception as e:
        print(f"❌ Nessun layer 'ple_layer' in {gpkg}: {e}")

    try:
        map_layer = gpd.read_file(gpkg, layer="map_layer")
        final_map_layers.append(map_layer)
    except Exception as e:
        print(f"❌ Nessun layer 'map_layer' in {gpkg}: {e}")

# Se ci sono layer validi, unirli e salvarli nel GPKG finale
if final_ple_layers:
    final_ple = gpd.pd.concat(final_ple_layers, ignore_index=True)
    final_ple.to_file(final_gpkg, layer="ple_layer", driver="GPKG")
    print(f"  ✔ Unito 'ple_layer' nel GPKG finale: {final_gpkg}")

if final_map_layers:
    final_map = gpd.pd.concat(final_map_layers, ignore_index=True)
    final_map.to_file(final_gpkg, layer="map_layer", driver="GPKG")
    print(f"  ✔ Unito 'map_layer' nel GPKG finale: {final_gpkg}")

# Eliminazione dei GPKG intermedi
for gpkg in gpkg_files:
    try:
        os.remove(gpkg)
        print(f"  🗑️ Eliminato GPKG intermedio: {gpkg}")
    except Exception as e:
        print(f"❌ Errore nell'eliminare {gpkg}: {e}")

print("\n✅ Processo COMPLETATO! Il file finale è:", final_gpkg)

