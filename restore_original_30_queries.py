import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv


# =========================================================
# 1. CONFIG
# =========================================================

OUTPUT_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)

BACKUP_PATH = (
    "data/metadata/"
    "query_subset_v2_26_backup.csv"
)

FIELDS = (
    "id,"
    "geometry,"
    "computed_geometry,"
    "captured_at,"
    "compass_angle,"
    "computed_compass_angle,"
    "sequence"
)


# =========================================================
# 2. IDS ORIGINAUX
# =========================================================

OLD_IDS = [
    "281697256836891",
    "472889960653931",
    "173698057991820",
    "141555101337124",
    "872645923597680",
    "342820367248999",
    "1180200166298335",
    "2194032487616206",
    "1106003470036201",
    "173777767979362",
    "288267562966408",
    "828279917812937",
    "563306154650990",
    "2894873010794086",
    "799421574300682",
    "485354839257022",
    "2951085711828430",
    "310234714037602",
    "275453527531880",
    "941083959999324",
    "333592151492072",
    "280291043810434",
    "526636091699811",
    "776055649761921",
    "138973908264709",
    "828796191072241",
    "1207001349764904",
    "1202230910991530",
    "1474701913443059",
    "223774435813473",
]


# =========================================================
# 3. TOKEN
# =========================================================

load_dotenv()

token = os.getenv(
    "MAPILLARY_TOKEN"
)

if not token:

    raise RuntimeError(
        "MAPILLARY_TOKEN introuvable dans .env"
    )


# =========================================================
# 4. BACKUP SÉCURITÉ
# =========================================================

if os.path.exists(
    OUTPUT_PATH
):

    if not os.path.exists(
        BACKUP_PATH
    ):

        current = pd.read_csv(
            OUTPUT_PATH
        )

        current.to_csv(
            BACKUP_PATH,
            index=False
        )

        print(
            "[BACKUP]",
            BACKUP_PATH
        )


# =========================================================
# 5. RÉCUPÉRATION MAPILLARY
# =========================================================

rows = []

failed = []


for index, image_id in enumerate(
    OLD_IDS,
    start=1
):

    print(
        f"[{index}/{len(OLD_IDS)}]",
        image_id
    )


    url = (
        f"https://graph.mapillary.com/"
        f"{image_id}"
    )


    params = {

        "fields":
            FIELDS,

        "access_token":
            token
    }


    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )


        response.raise_for_status()


        data = response.json()


    except Exception as exc:

        print(
            "[ERROR]",
            image_id,
            exc
        )

        failed.append(
            image_id
        )

        continue


    # =====================================================
    # 6. COORDONNÉES
    # =====================================================

    longitude = None
    latitude = None


    geometry = data.get(
        "geometry"
    )


    if (
        geometry
        and
        "coordinates"
        in geometry
        and
        len(
            geometry[
                "coordinates"
            ]
        )
        >=
        2
    ):

        longitude = float(
            geometry[
                "coordinates"
            ][0]
        )

        latitude = float(
            geometry[
                "coordinates"
            ][1]
        )


    computed_longitude = None
    computed_latitude = None


    computed_geometry = data.get(
        "computed_geometry"
    )


    if (
        computed_geometry
        and
        "coordinates"
        in computed_geometry
        and
        len(
            computed_geometry[
                "coordinates"
            ]
        )
        >=
        2
    ):

        computed_longitude = float(
            computed_geometry[
                "coordinates"
            ][0]
        )

        computed_latitude = float(
            computed_geometry[
                "coordinates"
            ][1]
        )


    # =====================================================
    # 7. HEADING
    # =====================================================

    computed_compass_angle = (
        data.get(
            "computed_compass_angle"
        )
    )


    compass_angle = (
        data.get(
            "compass_angle"
        )
    )


    if computed_compass_angle is not None:

        heading = float(
            computed_compass_angle
        )

    elif compass_angle is not None:

        heading = float(
            compass_angle
        )

    else:

        heading = None


    # =====================================================
    # 8. SÉQUENCE
    # =====================================================

    sequence = data.get(
        "sequence"
    )


    if isinstance(
        sequence,
        dict
    ):

        sequence = sequence.get(
            "id",
            ""
        )


    if sequence is None:

        sequence = ""


    # =====================================================
    # 9. LIGNE
    # =====================================================

    rows.append({

        "image_id":
            str(
                image_id
            ),

        "longitude":
            longitude,

        "latitude":
            latitude,

        "computed_longitude":
            computed_longitude,

        "computed_latitude":
            computed_latitude,

        "captured_at":
            data.get(
                "captured_at"
            ),

        "heading":
            heading,

        "computed_compass_angle":
            computed_compass_angle,

        "compass_angle":
            compass_angle,

        "sequence":
            str(
                sequence
            )
    })


    time.sleep(
        0.1
    )


# =========================================================
# 10. VÉRIFICATION
# =========================================================

print(
    "\n======================================"
)

print(
    "RÉCUPÉRATION TERMINÉE"
)

print(
    "======================================"
)


print(
    "Demandées :",
    len(
        OLD_IDS
    )
)


print(
    "Récupérées :",
    len(
        rows
    )
)


print(
    "Échecs :",
    len(
        failed
    )
)


if failed:

    print(
        "\nIDs en échec :"
    )

    for image_id in failed:

        print(
            "-",
            image_id
        )


# =========================================================
# 11. REFUSER D'ÉCRASER SI INCOMPLET
# =========================================================

if len(
    rows
) != len(
    OLD_IDS
):

    print(
        "\n[STOP] Le subset n'est pas complet."
    )

    print(
        "query_subset_v1.csv n'a pas été remplacé."
    )

    raise SystemExit(1)


# =========================================================
# 12. RESTAURER L'ORDRE ORIGINAL
# =========================================================

df = pd.DataFrame(
    rows
)


order_map = {

    image_id:
        index

    for index, image_id
    in enumerate(
        OLD_IDS
    )
}


df[
    "_order"
] = (
    df[
        "image_id"
    ]
    .map(
        order_map
    )
)


df = (
    df
    .sort_values(
        "_order"
    )
    .drop(
        columns=[
            "_order"
        ]
    )
    .reset_index(
        drop=True
    )
)


# =========================================================
# 13. SAUVEGARDE
# =========================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "\n======================================"
)

print(
    "SUBSET ORIGINAL RESTAURÉ"
)

print(
    "======================================"
)


print(
    "Fichier :",
    OUTPUT_PATH
)


print(
    "Nombre de queries :",
    len(
        df
    )
)


print(
    "Séquences uniques :",
    df[
        "sequence"
    ]
    .nunique()
)


print(
    "\nPremières lignes :"
)


print(
    df.head(
        5
    ).to_string(
        index=False
    )
)
