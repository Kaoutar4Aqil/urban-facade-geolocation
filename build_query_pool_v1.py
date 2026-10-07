import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv


# =========================================================
# 1. Configuration
# =========================================================

load_dotenv()

TOKEN = os.getenv("MAPILLARY_TOKEN")

if not TOKEN:
    raise ValueError("MAPILLARY_TOKEN introuvable dans .env")


# Zone autour de Paris utilisée actuellement
CENTER_LAT = 48.8566
CENTER_LON = 2.3522

# bbox assez large autour de la zone
DELTA_LAT = 0.004
DELTA_LON = 0.006

MIN_LON = CENTER_LON - DELTA_LON
MIN_LAT = CENTER_LAT - DELTA_LAT
MAX_LON = CENTER_LON + DELTA_LON
MAX_LAT = CENTER_LAT + DELTA_LAT


OUTPUT_PATH = (
    "data/metadata/"
    "query_pool_v1.csv"
)

REFERENCE_METADATA_PATH = (
    "data/processed/"
    "reference_pool_metadata_v2.csv"
)

OLD_QUERY_PATH = (
    "data/metadata/"
    "mapillary_test_images.csv"
)


# =========================================================
# 2. Paramètres
# =========================================================

LIMIT = 100

MAX_PAGES = 20

REQUEST_PAUSE = 0.15


# =========================================================
# 3. Charger IDs à exclure
# =========================================================

excluded_ids = set()


# anciennes queries
if os.path.exists(OLD_QUERY_PATH):

    old_queries = pd.read_csv(
        OLD_QUERY_PATH
    )

    old_queries[
        "image_id"
    ] = (
        old_queries[
            "image_id"
        ]
        .astype(str)
    )

    excluded_ids.update(
        old_queries[
            "image_id"
        ].tolist()
    )


# références
if os.path.exists(
    REFERENCE_METADATA_PATH
):

    refs = pd.read_csv(
        REFERENCE_METADATA_PATH
    )

    refs[
        "reference_image_id"
    ] = (
        refs[
            "reference_image_id"
        ]
        .astype(str)
    )

    excluded_ids.update(
        refs[
            "reference_image_id"
        ].tolist()
    )


print(
    "Nombre d'images exclues :",
    len(excluded_ids)
)


# =========================================================
# 4. Requête initiale Mapillary
# =========================================================

url = (
    "https://graph.mapillary.com/images"
)


params = {

    "access_token":
        TOKEN,

    "bbox":
        (
            f"{MIN_LON},"
            f"{MIN_LAT},"
            f"{MAX_LON},"
            f"{MAX_LAT}"
        ),

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
        LIMIT
}


# =========================================================
# 5. Pagination
# =========================================================

all_images = []

page = 1

next_url = url
next_params = params


while (
    next_url
    and page <= MAX_PAGES
):

    print(
        "\n======================================"
    )

    print(
        "PAGE :",
        page
    )

    print(
        "======================================"
    )


    try:

        response = requests.get(
            next_url,
            params=next_params,
            timeout=60
        )

    except requests.RequestException as e:

        print(
            "[ERROR]",
            e
        )

        break


    print(
        "HTTP status :",
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


    # quand on utilise paging["next"],
    # les paramètres sont déjà inclus dans l'URL
    next_params = None


    if not next_url:

        print(
            "Fin de pagination."
        )

        break


    page += 1

    time.sleep(
        REQUEST_PAUSE
    )


print(
    "\nNombre brut d'images récupérées :",
    len(all_images)
)


# =========================================================
# 6. Transformer en DataFrame
# =========================================================

rows = []


for image in all_images:

    image_id = str(
        image.get("id", "")
    )


    if not image_id:
        continue


    if image_id in excluded_ids:
        continue


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
        continue


    coordinates = geometry.get(
        "coordinates"
    )


    if (
        not coordinates
        or len(coordinates) < 2
    ):
        continue


    longitude = float(
        coordinates[0]
    )

    latitude = float(
        coordinates[1]
    )


    captured_at = image.get(
        "captured_at"
    )


    sequence = image.get(
        "sequence"
    )


    computed_heading = image.get(
        "computed_compass_angle"
    )


    raw_heading = image.get(
        "compass_angle"
    )


    # priorité à computed_compass_angle
    heading = (
        computed_heading
        if computed_heading is not None
        else raw_heading
    )


    if heading is None:
        continue


    try:

        heading = float(
            heading
        )

    except (
        TypeError,
        ValueError
    ):

        continue


    if not (
        0 <= heading < 360
    ):
        continue


    rows.append({

        "image_id":
            image_id,

        "longitude":
            longitude,

        "latitude":
            latitude,

        "captured_at":
            captured_at,

        "heading":
            heading,

        "computed_compass_angle":
            computed_heading,

        "compass_angle":
            raw_heading,

        "sequence":
            sequence
    })


df = pd.DataFrame(
    rows
)


# =========================================================
# 7. Supprimer doublons
# =========================================================

if not df.empty:

    df = (
        df
        .drop_duplicates(
            subset=[
                "image_id"
            ]
        )
        .reset_index(
            drop=True
        )
    )


print(
    "Après filtrage :",
    len(df)
)


# =========================================================
# 8. Statistiques sequences
# =========================================================

if not df.empty:

    sequence_counts = (
        df[
            "sequence"
        ]
        .value_counts(
            dropna=False
        )
    )


    print(
        "\nNombre de séquences :",
        df[
            "sequence"
        ]
        .nunique(
            dropna=True
        )
    )


    print(
        "\nTop 10 séquences :"
    )

    print(
        sequence_counts
        .head(10)
    )


# =========================================================
# 9. Sauvegarde
# =========================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "\n======================================"
)

print(
    "QUERY POOL V1 SAUVEGARDÉ"
)

print(
    "======================================"
)

print(
    OUTPUT_PATH
)

print(
    "Nombre total de candidates :",
    len(df)
)
