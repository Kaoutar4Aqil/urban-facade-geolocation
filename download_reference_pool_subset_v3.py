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
    raise ValueError(
        "MAPILLARY_TOKEN introuvable dans .env"
    )


METADATA_PATH = (
    "data/processed/"
    "reference_pool_subset_v3.csv"
)

OUTPUT_DIR = (
    "data/raw/"
    "reference_pool_subset_v3"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# =========================================================
# 2. Paramètres
# =========================================================

REQUEST_PAUSE = 0.10

API_TIMEOUT = 30

DOWNLOAD_TIMEOUT = 60


# =========================================================
# 3. Charger les références
# =========================================================

df = pd.read_csv(
    METADATA_PATH
)


df["building_id"] = (
    df["building_id"]
    .astype(str)
)


df["reference_image_id"] = (
    df["reference_image_id"]
    .astype(str)
)


print(
    "Nombre total de références dans le CSV :",
    len(df)
)


print(
    "Nombre de bâtiments :",
    df["building_id"].nunique()
)


# =========================================================
# 4. Supprimer doublons image
# =========================================================

unique_refs = (
    df[
        [
            "building_id",
            "reference_image_id"
        ]
    ]
    .drop_duplicates()
    .reset_index(
        drop=True
    )
)


print(
    "Nombre de couples bâtiment-référence uniques :",
    len(unique_refs)
)


# =========================================================
# 5. Fonction récupération URL Mapillary
# =========================================================

def get_image_url(
    image_id
):

    url = (
        f"https://graph.mapillary.com/"
        f"{image_id}"
    )


    params = {

        "access_token":
            TOKEN,

        "fields":
            (
                "id,"
                "thumb_2048_url"
            )
    }


    try:

        response = requests.get(
            url,
            params=params,
            timeout=API_TIMEOUT
        )

    except requests.RequestException as e:

        print(
            "[API ERROR]",
            image_id,
            e
        )

        return None


    if response.status_code != 200:

        print(
            "[API HTTP ERROR]",
            image_id,
            response.status_code
        )

        print(
            response.text
        )

        return None


    try:

        data = response.json()

    except ValueError:

        print(
            "[API JSON ERROR]",
            image_id
        )

        return None


    image_url = data.get(
        "thumb_2048_url"
    )


    if not image_url:

        print(
            "[NO URL]",
            image_id
        )

        return None


    return image_url


# =========================================================
# 6. Fonction téléchargement image
# =========================================================

def download_image(
    image_url,
    output_path
):

    try:

        response = requests.get(
            image_url,
            timeout=DOWNLOAD_TIMEOUT
        )

    except requests.RequestException as e:

        print(
            "[DOWNLOAD ERROR]",
            e
        )

        return False


    if response.status_code != 200:

        print(
            "[DOWNLOAD HTTP ERROR]",
            response.status_code
        )

        return False


    content = response.content


    if not content:

        print(
            "[EMPTY IMAGE]"
        )

        return False


    with open(
        output_path,
        "wb"
    ) as f:

        f.write(
            content
        )


    return True


# =========================================================
# 7. Téléchargement
# =========================================================

downloaded = 0

skipped = 0

failed = 0


total = len(
    unique_refs
)


for index, row in unique_refs.iterrows():

    building_id = str(
        row[
            "building_id"
        ]
    )

    image_id = str(
        row[
            "reference_image_id"
        ]
    )


    print(
        "\n======================================"
    )

    print(
        f"[{index + 1}/{total}]"
    )

    print(
        "Building :",
        building_id
    )

    print(
        "Reference :",
        image_id
    )


    # =====================================================
    # 8. Nom de fichier
    # =====================================================

    filename = (
        f"{building_id}_"
        f"{image_id}.jpg"
    )


    output_path = os.path.join(
        OUTPUT_DIR,
        filename
    )


    # =====================================================
    # 9. Déjà téléchargée
    # =====================================================

    if os.path.exists(
        output_path
    ):

        file_size = os.path.getsize(
            output_path
        )


        if file_size > 0:

            print(
                "[SKIP] Déjà présente :",
                output_path
            )

            skipped += 1

            continue


        else:

            print(
                "[WARNING] Fichier vide détecté, "
                "nouveau téléchargement."
            )


    # =====================================================
    # 10. Obtenir URL
    # =====================================================

    image_url = get_image_url(
        image_id
    )


    if not image_url:

        print(
            "[FAILED] URL introuvable"
        )

        failed += 1

        continue


    # =====================================================
    # 11. Télécharger
    # =====================================================

    success = download_image(
        image_url,
        output_path
    )


    if success:

        file_size = os.path.getsize(
            output_path
        )


        print(
            "[OK]",
            output_path
        )

        print(
            "Taille :",
            file_size,
            "bytes"
        )


        downloaded += 1

    else:

        print(
            "[FAILED]",
            image_id
        )

        failed += 1


    time.sleep(
        REQUEST_PAUSE
    )


# =========================================================
# 12. Résumé
# =========================================================

print(
    "\n======================================"
)

print(
    "TÉLÉCHARGEMENT TERMINÉ"
)

print(
    "======================================"
)


print(
    "Téléchargées :",
    downloaded
)


print(
    "Déjà présentes :",
    skipped
)


print(
    "Échecs :",
    failed
)


print(
    "Total attendu :",
    total
)


print(
    "\nDossier :",
    OUTPUT_DIR
)


# =========================================================
# 13. Vérification fichiers réellement présents
# =========================================================

jpg_files = [

    filename

    for filename in os.listdir(
        OUTPUT_DIR
    )

    if filename.lower().endswith(
        ".jpg"
    )
]


print(
    "\nNombre de JPG présents :",
    len(jpg_files)
)


# =========================================================
# 14. Vérification des références manquantes
# =========================================================

missing = []


for _, row in unique_refs.iterrows():

    building_id = str(
        row[
            "building_id"
        ]
    )

    image_id = str(
        row[
            "reference_image_id"
        ]
    )


    filename = (
        f"{building_id}_"
        f"{image_id}.jpg"
    )


    output_path = os.path.join(
        OUTPUT_DIR,
        filename
    )


    if not os.path.exists(
        output_path
    ):

        missing.append(
            {
                "building_id":
                    building_id,

                "reference_image_id":
                    image_id
            }
        )


# =========================================================
# 15. Rapport références manquantes
# =========================================================

print(
    "\nRéférences manquantes :",
    len(missing)
)


if missing:

    for item in missing:

        print(
            "-",
            item[
                "building_id"
            ],
            item[
                "reference_image_id"
            ]
        )


    missing_df = pd.DataFrame(
        missing
    )


    missing_path = (
        "data/processed/"
        "missing_reference_downloads_v3.csv"
    )


    missing_df.to_csv(
        missing_path,
        index=False
    )


    print(
        "\nListe des échecs sauvegardée :",
        missing_path
    )


else:

    print(
        "Toutes les références sont présentes."
    )


# =========================================================
# 16. Vérification finale
# =========================================================

successful_total = (
    downloaded
    +
    skipped
)


print(
    "\n======================================"
)

print(
    "VÉRIFICATION FINALE"
)

print(
    "======================================"
)


print(
    "Références disponibles :",
    successful_total,
    "/",
    total
)


if successful_total == total:

    print(
        "STATUS : OK"
    )

    print(
        "Toutes les références V3 "
        "sont disponibles."
    )

else:

    print(
        "STATUS : INCOMPLET"
    )

    print(
        "Certaines références n'ont pas "
        "pu être téléchargées."
    )
