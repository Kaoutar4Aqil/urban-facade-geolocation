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


METADATA_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)

OUTPUT_DIR = (
    "data/raw/"
    "query_subset_v1"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# =========================================================
# 2. Charger metadata
# =========================================================

df = pd.read_csv(
    METADATA_PATH
)

df["image_id"] = (
    df["image_id"]
    .astype(str)
)


print(
    "Nombre de queries à télécharger :",
    len(df)
)


# =========================================================
# 3. Récupérer URL Mapillary
# =========================================================

def get_image_url(image_id):

    url = (
        f"https://graph.mapillary.com/"
        f"{image_id}"
    )

    params = {
        "access_token": TOKEN,
        "fields": "id,thumb_2048_url"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
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
            "[HTTP ERROR]",
            image_id,
            response.status_code
        )

        return None


    data = response.json()

    return data.get(
        "thumb_2048_url"
    )


# =========================================================
# 4. Télécharger une image
# =========================================================

def download_image(
    image_url,
    output_path
):

    try:

        response = requests.get(
            image_url,
            timeout=60
        )

    except requests.RequestException:

        return False


    if response.status_code != 200:

        return False


    with open(
        output_path,
        "wb"
    ) as f:

        f.write(
            response.content
        )


    return True


# =========================================================
# 5. Télécharger toutes les queries
# =========================================================

downloaded = 0
skipped = 0
failed = 0


for index, row in df.iterrows():

    image_id = str(
        row["image_id"]
    )

    filename = (
        f"{image_id}.jpg"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        filename
    )


    print(
        f"\n[{index + 1}/{len(df)}]"
    )

    print(
        "Query :",
        image_id
    )


    if os.path.exists(
        output_path
    ):

        print(
            "[SKIP] Déjà présente"
        )

        skipped += 1
        continue


    image_url = get_image_url(
        image_id
    )


    if not image_url:

        print(
            "[ERROR] URL introuvable"
        )

        failed += 1
        continue


    success = download_image(
        image_url,
        output_path
    )


    if success:

        print(
            "[OK]",
            output_path
        )

        downloaded += 1

    else:

        print(
            "[ERROR] Téléchargement échoué"
        )

        failed += 1


    time.sleep(
        0.1
    )


# =========================================================
# 6. Résumé
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
    len(df)
)

print(
    "\nDossier :",
    OUTPUT_DIR
)
