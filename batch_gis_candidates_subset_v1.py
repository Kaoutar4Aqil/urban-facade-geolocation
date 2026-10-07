import math
import pandas as pd
import geopandas as gpd

from shapely.geometry import Point, LineString


# =========================================================
# 1. Chemins
# =========================================================

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
    "batch_gis_candidates_subset_v1.csv"
)


# =========================================================
# 2. Paramètres
# =========================================================

MAX_DISTANCE = 150

HALF_ANGLE = 25

NUMBER_OF_RAYS = 51

TOP_K = 10


# =========================================================
# 3. Charger queries
# =========================================================

queries = pd.read_csv(
    QUERY_PATH
)

queries["image_id"] = (
    queries["image_id"]
    .astype(str)
)


print(
    "Nombre de queries :",
    len(queries)
)


# =========================================================
# 4. Charger bâtiments
# =========================================================

buildings = gpd.read_file(
    BUILDINGS_PATH
)


if buildings.crs is None:
    buildings = buildings.set_crs(
        "EPSG:4326"
    )


# Projection métrique Paris
buildings_metric = buildings.to_crs(
    "EPSG:2154"
)


print(
    "Nombre de bâtiments :",
    len(buildings_metric)
)


# =========================================================
# 5. Fonction projection caméra
# =========================================================

def camera_to_metric(
    longitude,
    latitude
):

    camera = gpd.GeoSeries(
        [
            Point(
                longitude,
                latitude
            )
        ],
        crs="EPSG:4326"
    )

    camera_metric = camera.to_crs(
        "EPSG:2154"
    )

    return camera_metric.iloc[0]


# =========================================================
# 6. Création rayon
# =========================================================

def build_ray(
    camera_point,
    heading_deg,
    distance
):

    # heading Mapillary :
    # 0° = Nord
    # 90° = Est

    angle_rad = math.radians(
        heading_deg
    )

    dx = (
        distance
        * math.sin(
            angle_rad
        )
    )

    dy = (
        distance
        * math.cos(
            angle_rad
        )
    )


    end_point = Point(
        camera_point.x + dx,
        camera_point.y + dy
    )


    return LineString(
        [
            camera_point,
            end_point
        ]
    )


# =========================================================
# 7. Intersection la plus proche
# =========================================================

def nearest_intersection_distance(
    camera_point,
    geometry
):

    try:

        distance = (
            camera_point.distance(
                geometry
            )
        )

        return float(
            distance
        )

    except Exception:

        return None


# =========================================================
# 8. Pipeline GIS
# =========================================================

all_results = []


for query_index, query in queries.iterrows():

    query_id = str(
        query["image_id"]
    )

    longitude = float(
        query["longitude"]
    )

    latitude = float(
        query["latitude"]
    )

    heading = float(
        query["heading"]
    )


    print(
        "\n======================================"
    )

    print(
        "QUERY :",
        query_id
    )

    print(
        "Heading :",
        round(
            heading,
            2
        )
    )

    print(
        "======================================"
    )


    camera_point = camera_to_metric(
        longitude,
        latitude
    )


    # =====================================================
    # 9. Ignorer bâtiment contenant la caméra
    # =====================================================

    ignored_buildings = set()


    for idx, building in buildings_metric.iterrows():

        geometry = building.geometry

        if geometry is None:
            continue


        try:

            if (
                geometry.contains(
                    camera_point
                )
                or
                geometry.touches(
                    camera_point
                )
            ):

                ignored_buildings.add(
                    str(
                        building[
                            "building_id"
                        ]
                    )
                )

        except Exception:

            continue


    print(
        "Bâtiments ignorés :",
        ignored_buildings
    )


    # =====================================================
    # 10. Rayons dans le champ de vision
    # =====================================================

    ray_hits = {}


    angle_offsets = [

        -HALF_ANGLE
        +
        i
        * (
            (2 * HALF_ANGLE)
            /
            (NUMBER_OF_RAYS - 1)
        )

        for i in range(
            NUMBER_OF_RAYS
        )
    ]


    for offset in angle_offsets:

        ray_heading = (
            heading
            + offset
        ) % 360


        ray = build_ray(
            camera_point,
            ray_heading,
            MAX_DISTANCE
        )


        intersections = []


        for idx, building in buildings_metric.iterrows():

            building_id = str(
                building[
                    "building_id"
                ]
            )


            if (
                building_id
                in ignored_buildings
            ):

                continue


            geometry = (
                building.geometry
            )


            if geometry is None:
                continue


            try:

                if not ray.intersects(
                    geometry
                ):
                    continue

            except Exception:
                continue


            distance = (
                camera_point.distance(
                    geometry
                )
            )


            if (
                distance
                >
                MAX_DISTANCE
            ):

                continue


            intersections.append(
                (
                    distance,
                    building_id
                )
            )


        # -------------------------------------------------
        # Occlusion :
        # seul le premier bâtiment rencontré compte
        # -------------------------------------------------

        if intersections:

            intersections.sort(
                key=lambda x:
                    x[0]
            )


            nearest_distance, nearest_building = (
                intersections[0]
            )


            if (
                nearest_building
                not in ray_hits
            ):

                ray_hits[
                    nearest_building
                ] = {

                    "ray_hits":
                        0,

                    "min_distance":
                        nearest_distance
                }


            ray_hits[
                nearest_building
            ][
                "ray_hits"
            ] += 1


            ray_hits[
                nearest_building
            ][
                "min_distance"
            ] = min(

                ray_hits[
                    nearest_building
                ][
                    "min_distance"
                ],

                nearest_distance
            )


    # =====================================================
    # 11. Aucun candidat
    # =====================================================

    if not ray_hits:

        print(
            "Aucun bâtiment visible."
        )

        continue


    # =====================================================
    # 12. Calcul scores
    # =====================================================

    max_visibility = max(

        item[
            "ray_hits"
        ]

        for item in ray_hits.values()
    )


    query_results = []


    for building_id, info in ray_hits.items():

        hits = int(
            info[
                "ray_hits"
            ]
        )

        min_distance = float(
            info[
                "min_distance"
            ]
        )


        visibility_ratio = (
            hits
            /
            NUMBER_OF_RAYS
        )


        visibility_score = (
            hits
            /
            max_visibility
            if max_visibility > 0
            else 0
        )


        distance_score = (

            1.0
            -
            min(
                min_distance,
                MAX_DISTANCE
            )
            /
            MAX_DISTANCE
        )


        distance_score = max(
            0.0,
            min(
                1.0,
                distance_score
            )
        )


        gis_score = (

            0.7
            * visibility_score

            +

            0.3
            * distance_score
        )


        query_results.append({

            "query":
                query_id,

            "building_id":
                building_id,

            "ray_hits":
                hits,

            "visibility_ratio":
                visibility_ratio,

            "min_distance":
                min_distance,

            "visibility_score":
                visibility_score,

            "distance_score":
                distance_score,

            "gis_score":
                gis_score,

            "heading":
                heading
        })


    # =====================================================
    # 13. Trier Top-K
    # =====================================================

    query_results = sorted(

        query_results,

        key=lambda x:
            x[
                "gis_score"
            ],

        reverse=True
    )


    query_results = (
        query_results[
            :TOP_K
        ]
    )


    # =====================================================
    # 14. Affichage
    # =====================================================

    for result in query_results:

        print(

            result[
                "building_id"
            ],

            "| hits:",
            result[
                "ray_hits"
            ],

            "| visibility:",
            round(
                result[
                    "visibility_ratio"
                ],
                4
            ),

            "| distance:",
            round(
                result[
                    "min_distance"
                ],
                2
            ),

            "| GIS:",
            round(
                result[
                    "gis_score"
                ],
                4
            )
        )


    print(
        "Nombre de candidats :",
        len(query_results)
    )


    all_results.extend(
        query_results
    )


# =========================================================
# 15. Sauvegarde
# =========================================================

results_df = pd.DataFrame(
    all_results
)


results_df.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "\n======================================"
)

print(
    "GIS SUBSET V1 TERMINÉ"
)

print(
    "======================================"
)

print(
    "Fichier :",
    OUTPUT_PATH
)

print(
    "Nombre total de lignes :",
    len(results_df)
)


if not results_df.empty:

    print(
        "\nCandidats par query :"
    )

    print(
        results_df
        .groupby(
            "query"
        )
        .size()
    )
