import geopandas as gpd

input_path = "data/raw/osm/paris_buildings.geojson"
output_path = "data/processed/paris_buildings_clean.geojson"

# Charger les bâtiments
gdf = gpd.read_file(input_path)

print("Nombre initial de bâtiments :", len(gdf))

# Colonnes que nous voulons garder
columns = [
    "element",
    "id",
    "building",
    "building:levels",
    "height",
    "name",
    "addr:housenumber",
    "addr:street",
    "addr:postcode",
    "addr:city",
    "geometry"
]

# Garder seulement les colonnes présentes
columns = [col for col in columns if col in gdf.columns]

clean = gdf[columns].copy()

# Créer un identifiant simple pour notre projet
clean["building_id"] = [
    f"B{i:04d}"
    for i in range(1, len(clean) + 1)
]

# Calculer latitude / longitude du centroïde
projected = clean.to_crs(epsg=2154)

centroids = projected.geometry.centroid

centroids_wgs84 = gpd.GeoSeries(
    centroids,
    crs="EPSG:2154"
).to_crs(epsg=4326)

clean["longitude"] = centroids_wgs84.x
clean["latitude"] = centroids_wgs84.y

# Réorganiser les colonnes
final_columns = [
    "building_id",
    "element",
    "id",
    "building",
    "building:levels",
    "height",
    "name",
    "addr:housenumber",
    "addr:street",
    "addr:postcode",
    "addr:city",
    "latitude",
    "longitude",
    "geometry"
]

final_columns = [
    col for col in final_columns
    if col in clean.columns
]

clean = clean[final_columns]

# Sauvegarde
clean.to_file(
    output_path,
    driver="GeoJSON"
)

print("Nombre final de bâtiments :", len(clean))
print("Fichier sauvegardé :", output_path)

print("\nExemple :")
print(
    clean[
        [
            "building_id",
            "building",
            "name",
            "latitude",
            "longitude"
        ]
    ].head(10)
)
