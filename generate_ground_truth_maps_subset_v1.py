import os
import math
import pandas as pd
import geopandas as gpd
import folium

from shapely.geometry import Point


# =========================================================
# 1. Chemins
# =========================================================

QUERY_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)

GIS_PATH = (
    "data/processed/"
    "batch_gis_candidates_subset_v1.csv"
)

BUILDINGS_PATH = (
    "data/processed/"
    "paris_buildings_clean.geojson"
)

OUTPUT_DIR = (
    "data/processed/"
    "ground_truth_maps_subset_v1"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# =========================================================
# 2. Paramètres
# =========================================================

HEADING_LINE_LENGTH_METERS = 120

MAP_ZOOM_START = 19


# =========================================================
# 3. Charger les données
# =========================================================

queries = pd.read_csv(
    QUERY_PATH
)

gis = pd.read_csv(
    GIS_PATH
)

buildings = gpd.read_file(
    BUILDINGS_PATH
)


queries["image_id"] = (
    queries["image_id"]
    .astype(str)
)

gis["query"] = (
    gis["query"]
    .astype(str)
)

gis["building_id"] = (
    gis["building_id"]
    .astype(str)
)

buildings["building_id"] = (
    buildings["building_id"]
    .astype(str)
)


if buildings.crs is None:

    buildings = buildings.set_crs(
        "EPSG:4326"
    )


buildings_wgs84 = buildings.to_crs(
    "EPSG:4326"
)

buildings_metric = buildings.to_crs(
    "EPSG:2154"
)


# =========================================================
# 4. Fonctions utilitaires
# =========================================================

def get_query_coordinates(
    row
):

    lon = None
    lat = None


    if (
        "computed_longitude"
        in row.index
        and
        "computed_latitude"
        in row.index
        and
        pd.notna(
            row[
                "computed_longitude"
            ]
        )
        and
        pd.notna(
            row[
                "computed_latitude"
            ]
        )
    ):

        lon = float(
            row[
                "computed_longitude"
            ]
        )

        lat = float(
            row[
                "computed_latitude"
            ]
        )


    elif (
        "longitude"
        in row.index
        and
        "latitude"
        in row.index
        and
        pd.notna(
            row[
                "longitude"
            ]
        )
        and
        pd.notna(
            row[
                "latitude"
            ]
        )
    ):

        lon = float(
            row[
                "longitude"
            ]
        )

        lat = float(
            row[
                "latitude"
            ]
        )


    return lon, lat


def get_query_heading(
    row
):

    candidates = [

        "computed_compass_angle",
        "heading",
        "compass_angle"
    ]


    for column in candidates:

        if (
            column in row.index
            and
            pd.notna(
                row[
                    column
                ]
            )
        ):

            try:

                value = float(
                    row[
                        column
                    ]
                )

                if (
                    0
                    <= value
                    < 360
                ):

                    return value

            except (
                TypeError,
                ValueError
            ):

                pass


    return None


def point_wgs84_to_metric(
    longitude,
    latitude
):

    point_series = gpd.GeoSeries(
        [
            Point(
                longitude,
                latitude
            )
        ],
        crs="EPSG:4326"
    )


    return (
        point_series
        .to_crs(
            "EPSG:2154"
        )
        .iloc[0]
    )


def point_metric_to_wgs84(
    point
):

    point_series = gpd.GeoSeries(
        [
            point
        ],
        crs="EPSG:2154"
    )


    result = (
        point_series
        .to_crs(
            "EPSG:4326"
        )
        .iloc[0]
    )


    return (
        result.x,
        result.y
    )


def heading_endpoint(
    longitude,
    latitude,
    heading_degrees,
    length_meters
):

    camera_metric = (
        point_wgs84_to_metric(
            longitude,
            latitude
        )
    )


    angle_rad = math.radians(
        heading_degrees
    )


    dx = (
        length_meters
        *
        math.sin(
            angle_rad
        )
    )


    dy = (
        length_meters
        *
        math.cos(
            angle_rad
        )
    )


    endpoint_metric = Point(
        camera_metric.x
        + dx,

        camera_metric.y
        + dy
    )


    return point_metric_to_wgs84(
        endpoint_metric
    )


# =========================================================
# 5. Générer les cartes
# =========================================================

generated = 0

failed = 0


print(
    "Nombre total de queries :",
    len(queries)
)


for index, query_row in queries.iterrows():

    query_id = str(
        query_row[
            "image_id"
        ]
    )


    print(
        "\n======================================"
    )

    print(
        f"QUERY {index + 1}/{len(queries)} :",
        query_id
    )

    print(
        "======================================"
    )


    longitude, latitude = (
        get_query_coordinates(
            query_row
        )
    )


    heading = get_query_heading(
        query_row
    )


    if (
        longitude is None
        or
        latitude is None
    ):

        print(
            "[ERROR] Coordonnées introuvables."
        )

        failed += 1

        continue


    print(
        "Longitude :",
        longitude
    )

    print(
        "Latitude :",
        latitude
    )

    print(
        "Heading :",
        heading
    )


    # =====================================================
    # 6. Candidats GIS
    # =====================================================

    query_gis = (
        gis[
            gis[
                "query"
            ]
            ==
            query_id
        ]
        .copy()
        .sort_values(
            "gis_score",
            ascending=False
        )
    )


    candidate_ids = (
        query_gis[
            "building_id"
        ]
        .astype(str)
        .tolist()
    )


    print(
        "Nombre de candidats GIS :",
        len(candidate_ids)
    )


    # =====================================================
    # 7. Carte
    # =====================================================

    m = folium.Map(

        location=[
            latitude,
            longitude
        ],

        zoom_start=
            MAP_ZOOM_START,

        tiles=None
    )


    # =====================================================
    # 8. Caméra
    # =====================================================

    folium.CircleMarker(

        location=[
            latitude,
            longitude
        ],

        radius=7,

        weight=3,

        fill=True,

        fill_opacity=1,

        tooltip=(
            f"QUERY {query_id}"
        ),

        popup=(
            f"<b>QUERY</b><br>"
            f"ID: {query_id}<br>"
            f"Lon: {longitude}<br>"
            f"Lat: {latitude}<br>"
            f"Heading: {heading}"
        )

    ).add_to(
        m
    )


    # =====================================================
    # 9. Ligne du heading
    # =====================================================

    if heading is not None:

        end_lon, end_lat = (
            heading_endpoint(
                longitude,
                latitude,
                heading,
                HEADING_LINE_LENGTH_METERS
            )
        )


        folium.PolyLine(

            locations=[
                [
                    latitude,
                    longitude
                ],
                [
                    end_lat,
                    end_lon
                ]
            ],

            weight=5,

            opacity=0.9,

            tooltip=(
                f"Heading {heading:.2f}°"
            )

        ).add_to(
            m
        )


        folium.CircleMarker(

            location=[
                end_lat,
                end_lon
            ],

            radius=4,

            fill=True,

            fill_opacity=1,

            tooltip="Fin du heading"

        ).add_to(
            m
        )


    # =====================================================
    # 10. Bâtiments voisins
    # =====================================================

    camera_metric = (
        point_wgs84_to_metric(
            longitude,
            latitude
        )
    )


    buildings_metric_copy = (
        buildings_metric.copy()
    )


    buildings_metric_copy[
        "distance_camera"
    ] = (
        buildings_metric_copy
        .geometry
        .distance(
            camera_metric
        )
    )


    nearby_ids = (
        buildings_metric_copy[
            buildings_metric_copy[
                "distance_camera"
            ]
            <= 180
        ][
            "building_id"
        ]
        .astype(str)
        .tolist()
    )


    nearby_buildings = (
        buildings_wgs84[
            buildings_wgs84[
                "building_id"
            ]
            .astype(str)
            .isin(
                nearby_ids
            )
        ]
        .copy()
    )


    # =====================================================
    # 11. Dessiner bâtiments
    # =====================================================

    for _, building_row in (
        nearby_buildings.iterrows()
    ):

        building_id = str(
            building_row[
                "building_id"
            ]
        )


        geometry = (
            building_row.geometry
        )


        is_candidate = (
            building_id
            in candidate_ids
        )


        gis_score = None


        if is_candidate:

            score_rows = (
                query_gis[
                    query_gis[
                        "building_id"
                    ]
                    ==
                    building_id
                ]
            )


            if not score_rows.empty:

                gis_score = float(
                    score_rows.iloc[0][
                        "gis_score"
                    ]
                )


        if is_candidate:

            tooltip = (
                f"{building_id} | GIS candidate"
            )

            if gis_score is not None:

                tooltip += (
                    f" | score={gis_score:.4f}"
                )

        else:

            tooltip = (
                f"{building_id}"
            )


        style = {

            "weight":
                4
                if is_candidate
                else 1,

            "fillOpacity":
                0.35
                if is_candidate
                else 0.05
        }


        folium.GeoJson(

            geometry.__geo_interface__,

            style_function=(
                lambda feature,
                style=style:
                style
            ),

            tooltip=tooltip

        ).add_to(
            m
        )


        # =================================================
        # Label bâtiment
        # =================================================

        try:

            centroid = (
                geometry.centroid
            )


            folium.Marker(

                location=[
                    centroid.y,
                    centroid.x
                ],

                icon=folium.DivIcon(

                    html=(
                        "<div style='"
                        "font-size:11px;"
                        "font-weight:bold;"
                        "background:white;"
                        "border:1px solid black;"
                        "padding:2px;"
                        "'>"
                        f"{building_id}"
                        "</div>"
                    )
                )

            ).add_to(
                m
            )

        except Exception:

            pass


    # =====================================================
    # 12. Bloc informations
    # =====================================================

    candidate_text = (
        "<br>".join(
            [
                (
                    f"{row['building_id']} "
                    f"(GIS={row['gis_score']:.4f})"
                )

                for _, row
                in query_gis.iterrows()
            ]
        )
    )


    if not candidate_text:

        candidate_text = (
            "Aucun candidat GIS"
        )


    html_info = f"""
    <div style="
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 9999;
        background-color: white;
        border: 2px solid black;
        padding: 10px;
        font-size: 13px;
        max-width: 330px;
    ">
        <b>Ground Truth Annotation</b><br><br>

        <b>Query:</b>
        {query_id}
        <br>

        <b>Coordinates:</b>
        {latitude:.7f},
        {longitude:.7f}
        <br>

        <b>Heading:</b>
        {heading}
        <br><br>

        <b>GIS candidates:</b>
        <br>

        {candidate_text}

        <br><br>

        <b>Instruction:</b><br>
        Identify the building actually
        visible in the query image.
        Do not choose automatically from
        GIS or fusion prediction.
    </div>
    """


    m.get_root().html.add_child(
        folium.Element(
            html_info
        )
    )


    # =====================================================
    # 13. Sauvegarder
    # =====================================================

    output_path = os.path.join(

        OUTPUT_DIR,

        f"{query_id}.html"
    )


    m.save(
        output_path
    )


    print(
        "[OK]",
        output_path
    )


    generated += 1


# =========================================================
# 14. Résumé final
# =========================================================

print(
    "\n======================================"
)

print(
    "GÉNÉRATION TERMINÉE"
)

print(
    "======================================"
)


print(
    "Cartes générées :",
    generated
)


print(
    "Échecs :",
    failed
)


print(
    "Dossier :",
    OUTPUT_DIR
)
