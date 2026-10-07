import os
import time
import math
import requests
import pandas as pd
import geopandas as gpd

from dotenv import load_dotenv
from shapely.geometry import Point
from shapely.ops import nearest_points


# =========================================================
# 1. Configuration
# =========================================================

load_dotenv()

TOKEN = os.getenv("MAPILLARY_TOKEN")

if not TOKEN:
    raise ValueError(
        "MAPILLARY_TOKEN introuvable dans .env"
    )


GIS_PATH = (
    "data/processed/"
    "batch_gis_candidates_subset_v1.csv"
)

QUERY_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)

BUILDINGS_PATH = (
    "data/processed/"
    "paris_buildings_clean.geojson"
)

OUTPUT_PATH = (
    "data/processed/"
    "reference_pool_subset_v3.csv"
)


# =========================================================
# 2. Paramètres
# =========================================================

MAPILLARY_LIMIT = 100

MAX_PAGES_PER_BUILDING = 5

MAX_REFERENCES_PER_BUILDING = 8

MAX_REFERENCE_DISTANCE = 200

MAX_ANGLE_DIFFERENCE = 50

SEARCH_MARGIN_DEG = 0.003

REQUEST_PAUSE = 0.10


# =========================================================
# 3. Charger les données
# =========================================================

gis = pd.read_csv(
    GIS_PATH
)

queries = pd.read_csv(
    QUERY_PATH
)

buildings = gpd.read_file(
    BUILDINGS_PATH
)


gis["query"] = (
    gis["query"]
    .astype(str)
)

gis["building_id"] = (
    gis["building_id"]
    .astype(str)
)

queries["image_id"] = (
    queries["image_id"]
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


buildings_wgs84[
    "building_id"
] = (
    buildings_wgs84[
        "building_id"
    ]
    .astype(str)
)

buildings_metric[
    "building_id"
] = (
    buildings_metric[
        "building_id"
    ]
    .astype(str)
)


# =========================================================
# 4. Query IDs à exclure
# =========================================================

excluded_query_ids = set(
    queries[
        "image_id"
    ]
    .dropna()
    .astype(str)
    .tolist()
)


print(
    "Queries exclues :",
    len(excluded_query_ids)
)


# =========================================================
# 5. Bâtiments candidats uniques
# =========================================================

candidate_buildings = (
    gis[
        "building_id"
    ]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


candidate_buildings = sorted(
    candidate_buildings
)


print(
    "\nNombre de bâtiments candidats :",
    len(candidate_buildings)
)


for building_id in candidate_buildings:

    print(
        "-",
        building_id
    )


# =========================================================
# 6. Projection d'un point WGS84 -> Lambert 93
# =========================================================

def point_to_metric(
    longitude,
    latitude
):

    series = gpd.GeoSeries(
        [
            Point(
                longitude,
                latitude
            )
        ],
        crs="EPSG:4326"
    )

    projected = series.to_crs(
        "EPSG:2154"
    )

    return projected.iloc[0]


# =========================================================
# 7. Bearing métrique
# =========================================================

def bearing_metric(
    start_point,
    end_point
):

    dx = (
        end_point.x
        -
        start_point.x
    )

    dy = (
        end_point.y
        -
        start_point.y
    )


    angle = math.degrees(
        math.atan2(
            dx,
            dy
        )
    )


    return (
        angle
        + 360
    ) % 360


# =========================================================
# 8. Différence angulaire
# =========================================================

def angular_difference(
    angle1,
    angle2
):

    diff = abs(
        angle1
        -
        angle2
    ) % 360


    return min(
        diff,
        360 - diff
    )


# =========================================================
# 9. Récupération coordonnées Mapillary
# =========================================================

def get_image_coordinates(
    image
):

    geometry = (
        image.get(
            "computed_geometry"
        )
        or
        image.get(
            "geometry"
        )
    )


    if not geometry:
        return None


    coordinates = geometry.get(
        "coordinates"
    )


    if (
        coordinates is None
        or len(coordinates) < 2
    ):
        return None


    try:

        longitude = float(
            coordinates[0]
        )

        latitude = float(
            coordinates[1]
        )

    except (
        TypeError,
        ValueError
    ):

        return None


    return (
        longitude,
        latitude
    )


# =========================================================
# 10. Heading Mapillary
# =========================================================

def get_heading(
    image
):

    computed = image.get(
        "computed_compass_angle"
    )

    raw = image.get(
        "compass_angle"
    )


    value = (
        computed
        if computed is not None
        else raw
    )


    if value is None:
        return None


    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return None


    if not (
        0 <= value < 360
    ):
        return None


    return value


# =========================================================
# 11. Recherche Mapillary avec pagination
# =========================================================

def search_mapillary_images(
    bbox
):

    url = (
        "https://graph.mapillary.com/"
        "images"
    )


    params = {

        "access_token":
            TOKEN,

        "bbox":
            bbox,

        "fields":
            (
                "id,"
                "geometry,"
                "computed_geometry,"
                "captured_at,"
                "compass_angle,"
                "computed_compass_angle,"
                "sequence"
            ),

        "limit":
            MAPILLARY_LIMIT
    }


    all_images = []

    next_url = url
    next_params = params

    page = 1


    while (
        next_url
        and
        page <= MAX_PAGES_PER_BUILDING
    ):

        try:

            response = requests.get(
                next_url,
                params=next_params,
                timeout=60
            )

        except requests.RequestException as e:

            print(
                "[API ERROR]",
                e
            )

            break


        print(
            "Page",
            page,
            "| HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                response.text
            )

            break


        data = response.json()


        images = data.get(
            "data",
            []
        )


        print(
            "Images reçues :",
            len(images)
        )


        all_images.extend(
            images
        )


        paging = data.get(
            "paging",
            {}
        )


        next_url = paging.get(
            "next"
        )


        next_params = None


        if not next_url:
            break


        page += 1

        time.sleep(
            REQUEST_PAUSE
        )


    # -----------------------------------------------------
    # Supprimer doublons
    # -----------------------------------------------------

    unique = {}


    for image in all_images:

        image_id = str(
            image.get(
                "id",
                ""
            )
        )


        if image_id:

            unique[
                image_id
            ] = image


    return list(
        unique.values()
    )


# =========================================================
# 12. Construction pool de références
# =========================================================

all_references = []


for building_index, building_id in enumerate(
    candidate_buildings,
    start=1
):

    print(
        "\n======================================"
    )

    print(
        f"BUILDING {building_index}/"
        f"{len(candidate_buildings)} :",
        building_id
    )

    print(
        "======================================"
    )


    building_wgs = (
        buildings_wgs84[
            buildings_wgs84[
                "building_id"
            ]
            ==
            building_id
        ]
    )


    building_metric_row = (
        buildings_metric[
            buildings_metric[
                "building_id"
            ]
            ==
            building_id
        ]
    )


    if (
        building_wgs.empty
        or
        building_metric_row.empty
    ):

        print(
            "Bâtiment introuvable."
        )

        continue


    geometry_wgs = (
        building_wgs
        .iloc[0]
        .geometry
    )


    geometry_metric = (
        building_metric_row
        .iloc[0]
        .geometry
    )


    if (
        geometry_wgs is None
        or
        geometry_metric is None
    ):

        continue


    # =====================================================
    # 13. Bounding box autour du bâtiment
    # =====================================================

    minx, miny, maxx, maxy = (
        geometry_wgs.bounds
    )


    minx -= SEARCH_MARGIN_DEG
    maxx += SEARCH_MARGIN_DEG

    miny -= SEARCH_MARGIN_DEG
    maxy += SEARCH_MARGIN_DEG


    bbox = (
        f"{minx},"
        f"{miny},"
        f"{maxx},"
        f"{maxy}"
    )


    images = search_mapillary_images(
        bbox
    )


    print(
        "Total images API :",
        len(images)
    )


    candidates = []


    # =====================================================
    # 14. Filtrer les images candidates
    # =====================================================

    for image in images:

        image_id = str(
            image.get(
                "id",
                ""
            )
        )


        if not image_id:
            continue


        # -------------------------------------------------
        # Une query ne peut jamais devenir référence
        # -------------------------------------------------

        if (
            image_id
            in excluded_query_ids
        ):

            continue


        sequence = image.get(
            "sequence"
        )


        if sequence is not None:

            sequence = str(
                sequence
            )


        coords = get_image_coordinates(
            image
        )


        if coords is None:
            continue


        longitude, latitude = coords


        heading = get_heading(
            image
        )


        if heading is None:
            continue


        camera_metric = point_to_metric(
            longitude,
            latitude
        )


        # -------------------------------------------------
        # Distance caméra -> bâtiment
        # -------------------------------------------------

        try:

            distance = (
                camera_metric.distance(
                    geometry_metric
                )
            )

        except Exception:

            continue


        if (
            distance
            >
            MAX_REFERENCE_DISTANCE
        ):

            continue


        # -------------------------------------------------
        # Point le plus proche sur le bâtiment
        # -------------------------------------------------

        try:

            nearest_building_point = (
                nearest_points(
                    camera_metric,
                    geometry_metric
                )[1]
            )

        except Exception:

            continue


        # -------------------------------------------------
        # Direction vers le bâtiment
        # -------------------------------------------------

        target_bearing = (
            bearing_metric(
                camera_metric,
                nearest_building_point
            )
        )


        angle_diff = (
            angular_difference(
                heading,
                target_bearing
            )
        )


        if (
            angle_diff
            >
            MAX_ANGLE_DIFFERENCE
        ):

            continue


        # =================================================
        # IMPORTANT V3
        #
        # Pas de filtre d'occlusion ici.
        #
        # Le but est de maximiser le recall du pool.
        # La validation visuelle sera faite ensuite avec
        # SIFT + RANSAC.
        # =================================================


        # -------------------------------------------------
        # Scores
        # -------------------------------------------------

        angle_score = (
            1.0
            -
            (
                angle_diff
                /
                MAX_ANGLE_DIFFERENCE
            )
        )


        distance_score = (
            1.0
            -
            (
                min(
                    distance,
                    MAX_REFERENCE_DISTANCE
                )
                /
                MAX_REFERENCE_DISTANCE
            )
        )


        reference_score = (
            0.7
            * angle_score
            +
            0.3
            * distance_score
        )


        candidates.append({

            "building_id":
                building_id,

            "reference_image_id":
                image_id,

            "longitude":
                longitude,

            "latitude":
                latitude,

            "heading":
                heading,

            "target_bearing":
                target_bearing,

            "angle_difference":
                angle_diff,

            "distance_to_building":
                distance,

            "angle_score":
                angle_score,

            "distance_score":
                distance_score,

            "reference_score":
                reference_score,

            "sequence":
                sequence,

            "captured_at":
                image.get(
                    "captured_at"
                )
        })


    # =====================================================
    # 15. Trier les références
    # =====================================================

    candidates = sorted(

        candidates,

        key=lambda x: (

            -x[
                "reference_score"
            ],

            x[
                "angle_difference"
            ],

            x[
                "distance_to_building"
            ]
        )
    )


    selected = candidates[
        :MAX_REFERENCES_PER_BUILDING
    ]


    if not selected:

        print(
            "Aucune référence valide."
        )

        continue


    print(
        "\nRéférences sélectionnées :"
    )


    for ref in selected:

        print(

            ref[
                "reference_image_id"
            ],

            "| angle diff:",
            round(
                ref[
                    "angle_difference"
                ],
                2
            ),

            "° | distance:",
            round(
                ref[
                    "distance_to_building"
                ],
                2
            ),

            "m | score:",
            round(
                ref[
                    "reference_score"
                ],
                4
            ),

            "| sequence:",
            ref[
                "sequence"
            ]
        )


    all_references.extend(
        selected
    )


# =========================================================
# 16. DataFrame final
# =========================================================

reference_df = pd.DataFrame(
    all_references
)


# =========================================================
# 17. Sauvegarde
# =========================================================

reference_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 18. Résumé
# =========================================================

print(
    "\n======================================"
)

print(
    "REFERENCE POOL SUBSET V3 TERMINÉ"
)

print(
    "======================================"
)


print(
    "Fichier :",
    OUTPUT_PATH
)


print(
    "Nombre total de références :",
    len(reference_df)
)


covered_buildings = 0


if not reference_df.empty:

    covered_buildings = (
        reference_df[
            "building_id"
        ]
        .nunique()
    )


print(
    "Nombre de bâtiments couverts :",
    covered_buildings
)


print(
    "Nombre total de bâtiments candidats :",
    len(candidate_buildings)
)


if len(candidate_buildings) > 0:

    coverage = (
        covered_buildings
        /
        len(candidate_buildings)
        *
        100
    )

else:

    coverage = 0


print(
    "Couverture :",
    f"{coverage:.2f}%"
)


if not reference_df.empty:

    print(
        "\nRéférences par bâtiment :"
    )


    print(
        reference_df
        .groupby(
            "building_id"
        )
        .size()
    )


    print(
        "\nNombre de séquences de référence :",
        reference_df[
            "sequence"
        ]
        .nunique(
            dropna=True
        )
    )


# =========================================================
# 19. Bâtiments sans références
# =========================================================

covered_set = set()


if not reference_df.empty:

    covered_set = set(
        reference_df[
            "building_id"
        ]
        .astype(str)
        .unique()
    )


missing_buildings = [

    building_id

    for building_id
    in candidate_buildings

    if building_id
    not in covered_set
]


print(
    "\nBâtiments sans référence :",
    len(missing_buildings)
)


for building_id in missing_buildings:

    print(
        "-",
        building_id
    )


print(
    "\nNOTE :"
)

print(
    "Les références de même séquence qu'une query "
    "ne sont pas supprimées ici."
)

print(
    "Le filtrage same-sequence sera effectué "
    "query par query pendant SIFT/RANSAC."
)
