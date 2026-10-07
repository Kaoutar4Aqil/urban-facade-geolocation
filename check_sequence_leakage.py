import os
import requests
import pandas as pd

from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("MAPILLARY_TOKEN")

if not TOKEN:
    raise ValueError("MAPILLARY_TOKEN introuvable")


PREDICTIONS_PATH = (
    "data/processed/"
    "batch_final_predictions_v2.csv"
)


df = pd.read_csv(
    PREDICTIONS_PATH
)


df["query"] = (
    df["query"]
    .astype(str)
)


# garder uniquement Top-1
top1 = df[
    df["rank"] == 1
].copy()


def get_metadata(image_id):

    url = (
        f"https://graph.mapillary.com/"
        f"{image_id}"
    )

    params = {
        "access_token": TOKEN,
        "fields": (
            "id,"
            "captured_at,"
            "sequence"
        )
    }


    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

    except requests.RequestException as e:

        print(
            "[ERROR]",
            image_id,
            e
        )

        return None


    if response.status_code != 200:

        print(
            "[HTTP ERROR]",
            image_id,
            response.status_code,
            response.text
        )

        return None


    return response.json()


print(
    "\n======================================"
)

print(
    "VÉRIFICATION SEQUENCE LEAKAGE"
)

print(
    "======================================"
)


results = []


for _, row in top1.iterrows():

    query_id = str(
        row["query"]
    )

    building_id = str(
        row["building_id"]
    )


    if pd.isna(
        row["best_reference"]
    ):

        continue


    reference_id = str(
        int(
            float(
                row["best_reference"]
            )
        )
    )


    query_meta = get_metadata(
        query_id
    )

    reference_meta = get_metadata(
        reference_id
    )


    if (
        query_meta is None
        or reference_meta is None
    ):

        continue


    query_sequence = (
        query_meta.get(
            "sequence"
        )
    )

    reference_sequence = (
        reference_meta.get(
            "sequence"
        )
    )


    same_sequence = (
        query_sequence
        is not None
        and reference_sequence
        is not None
        and query_sequence
        == reference_sequence
    )


    print(
        "\nQUERY :",
        query_id
    )

    print(
        "Building :",
        building_id
    )

    print(
        "Reference :",
        reference_id
    )

    print(
        "Query sequence :",
        query_sequence
    )

    print(
        "Reference sequence :",
        reference_sequence
    )

    print(
        "Même séquence :",
        same_sequence
    )


    results.append({
        "query":
            query_id,

        "building_id":
            building_id,

        "reference_id":
            reference_id,

        "query_sequence":
            query_sequence,

        "reference_sequence":
            reference_sequence,

        "same_sequence":
            same_sequence,

        "query_captured_at":
            query_meta.get(
                "captured_at"
            ),

        "reference_captured_at":
            reference_meta.get(
                "captured_at"
            )
    })


result_df = pd.DataFrame(
    results
)


output_path = (
    "data/processed/"
    "sequence_leakage_check.csv"
)


result_df.to_csv(
    output_path,
    index=False
)


print(
    "\n======================================"
)

print(
    "Résultats sauvegardés :"
)

print(
    output_path
)
