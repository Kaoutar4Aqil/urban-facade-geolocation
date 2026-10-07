import os
import pandas as pd


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

PREDICTION_PATH = (
    "data/processed/"
    "batch_final_predictions_subset_v1_clean.csv"
)

OUTPUT_PATH = (
    "data/metadata/"
    "ground_truth_subset_v1.csv"
)


# =========================================================
# 2. Charger les données
# =========================================================

queries = pd.read_csv(
    QUERY_PATH
)


queries["image_id"] = (
    queries["image_id"]
    .astype(str)
)


print(
    "Nombre total de queries :",
    len(queries)
)


# =========================================================
# 3. Charger éventuellement les candidats GIS
# =========================================================

if os.path.exists(
    GIS_PATH
):

    gis = pd.read_csv(
        GIS_PATH
    )

    gis["query"] = (
        gis["query"]
        .astype(str)
    )

    gis["building_id"] = (
        gis["building_id"]
        .astype(str)
    )

else:

    gis = pd.DataFrame()


# =========================================================
# 4. Charger éventuellement les prédictions
#
# ATTENTION :
# elles servent seulement comme information de contrôle.
# Elles ne deviennent PAS le ground truth.
# =========================================================

if os.path.exists(
    PREDICTION_PATH
):

    predictions = pd.read_csv(
        PREDICTION_PATH
    )

    predictions["query"] = (
        predictions["query"]
        .astype(str)
    )

    predictions["building_id"] = (
        predictions["building_id"]
        .astype(str)
    )

else:

    predictions = pd.DataFrame()


# =========================================================
# 5. Construire les lignes ground truth
# =========================================================

rows = []


for _, query_row in queries.iterrows():

    query_id = str(
        query_row[
            "image_id"
        ]
    )


    sequence = ""

    if (
        "sequence"
        in query_row.index
        and
        pd.notna(
            query_row[
                "sequence"
            ]
        )
    ):

        sequence = str(
            query_row[
                "sequence"
            ]
        )


    # =====================================================
    # Candidat GIS Top-1
    # Information seulement
    # =====================================================

    gis_top1 = ""

    gis_candidate_count = 0


    if not gis.empty:

        query_gis = (
            gis[
                gis[
                    "query"
                ]
                ==
                query_id
            ]
            .copy()
        )


        gis_candidate_count = len(
            query_gis
        )


        if not query_gis.empty:

            query_gis = (
                query_gis
                .sort_values(
                    "gis_score",
                    ascending=False
                )
            )


            gis_top1 = str(
                query_gis.iloc[0][
                    "building_id"
                ]
            )


    # =====================================================
    # Fusion Top-1
    # Information seulement
    # =====================================================

    fusion_top1 = ""


    if not predictions.empty:

        query_prediction = (

            predictions[
                predictions[
                    "query"
                ]
                ==
                query_id
            ]
        )


        if not query_prediction.empty:

            if (
                "rank"
                in query_prediction.columns
            ):

                top1 = (
                    query_prediction[
                        query_prediction[
                            "rank"
                        ]
                        ==
                        1
                    ]
                )

            else:

                top1 = (
                    query_prediction
                    .sort_values(
                        "final_score",
                        ascending=False
                    )
                    .head(1)
                )


            if not top1.empty:

                fusion_top1 = str(
                    top1.iloc[0][
                        "building_id"
                    ]
                )


    # =====================================================
    # Ligne finale
    # =====================================================

    rows.append({

        "query_id":
            query_id,

        "sequence":
            sequence,

        "true_building_id":
            "",

        "status":
            "pending",

        "verification_method":
            "",

        "notes":
            "",

        "gis_candidate_count":
            gis_candidate_count,

        "gis_top1_for_reference_only":
            gis_top1,

        "fusion_top1_for_reference_only":
            fusion_top1
    })


# =========================================================
# 6. DataFrame final
# =========================================================

ground_truth = pd.DataFrame(
    rows
)


# =========================================================
# 7. Sauvegarde
# =========================================================

ground_truth.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 8. Résumé
# =========================================================

print(
    "\n======================================"
)

print(
    "GROUND TRUTH SUBSET V1 CRÉÉ"
)

print(
    "======================================"
)


print(
    "Fichier :",
    OUTPUT_PATH
)


print(
    "Nombre de lignes :",
    len(
        ground_truth
    )
)


print(
    "Status pending :",
    (
        ground_truth[
            "status"
        ]
        ==
        "pending"
    ).sum()
)


print(
    "Queries sans candidat GIS :",
    (
        ground_truth[
            "gis_candidate_count"
        ]
        ==
        0
    ).sum()
)


print(
    "\n======================================"
)

print(
    "APERÇU"
)

print(
    "======================================"
)


print(

    ground_truth[
        [
            "query_id",
            "true_building_id",
            "status",
            "gis_candidate_count",
            "gis_top1_for_reference_only",
            "fusion_top1_for_reference_only"
        ]
    ]
    .to_string(
        index=False
    )
)


print(
    "\nIMPORTANT :"
)

print(
    "Les colonnes gis_top1_for_reference_only "
    "et fusion_top1_for_reference_only "
    "sont uniquement informatives."
)

print(
    "Elles ne doivent PAS être copiées "
    "automatiquement dans true_building_id."
)

print(
    "Le true_building_id doit être rempli "
    "manuellement après vérification indépendante."
)
