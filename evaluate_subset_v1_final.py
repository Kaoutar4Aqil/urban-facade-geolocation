import os
import pandas as pd


# =========================================================
# 1. CHEMINS
# =========================================================

GROUND_TRUTH_PATH = (
    "data/metadata/"
    "ground_truth_subset_v1.csv"
)

GIS_PATH = (
    "data/processed/"
    "batch_gis_candidates_subset_v1.csv"
)

FUSION_PATH = (
    "data/processed/"
    "batch_final_predictions_subset_v1_clean.csv"
)

OUTPUT_DETAILS_PATH = (
    "data/processed/"
    "evaluation_subset_v1_details.csv"
)

OUTPUT_SUMMARY_PATH = (
    "data/processed/"
    "evaluation_subset_v1_summary.csv"
)


# =========================================================
# 2. CHARGEMENT
# =========================================================

ground_truth = pd.read_csv(
    GROUND_TRUTH_PATH
)

gis = pd.read_csv(
    GIS_PATH
)

fusion = pd.read_csv(
    FUSION_PATH
)


# =========================================================
# 3. NORMALISATION DES TYPES
# =========================================================

ground_truth["query_id"] = (
    ground_truth["query_id"]
    .astype(str)
)

ground_truth["true_building_id"] = (
    ground_truth["true_building_id"]
    .fillna("")
    .astype(str)
)

ground_truth["status"] = (
    ground_truth["status"]
    .fillna("")
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


fusion["query"] = (
    fusion["query"]
    .astype(str)
)

fusion["building_id"] = (
    fusion["building_id"]
    .astype(str)
)


# =========================================================
# 4. INFORMATIONS GÉNÉRALES
# =========================================================

total_queries = len(
    ground_truth
)


verified_gt = (
    ground_truth[
        (
            ground_truth["status"]
            .str.lower()
            ==
            "verified"
        )
        &
        (
            ground_truth[
                "true_building_id"
            ]
            !=
            ""
        )
    ]
    .copy()
)


pending_gt = (
    ground_truth[
        ground_truth["status"]
        .str.lower()
        !=
        "verified"
    ]
)


print(
    "======================================"
)

print(
    "ÉVALUATION FINALE - SUBSET V1"
)

print(
    "======================================"
)


print(
    "Queries totales :",
    total_queries
)

print(
    "Ground truth vérifiés :",
    len(verified_gt)
)

print(
    "Ground truth non vérifiés :",
    len(pending_gt)
)


# =========================================================
# 5. SI AUCUN GT VÉRIFIÉ
# =========================================================

if verified_gt.empty:

    print(
        "\nAucun ground truth vérifié."
    )

    print(
        "Compléter true_building_id et passer "
        "status à verified avant l'évaluation."
    )

    raise SystemExit(0)


# =========================================================
# 6. ÉVALUATION PAR QUERY
# =========================================================

rows = []


for _, gt_row in verified_gt.iterrows():

    query_id = str(
        gt_row[
            "query_id"
        ]
    )

    true_building = str(
        gt_row[
            "true_building_id"
        ]
    )


    # =====================================================
    # GIS CANDIDATES
    # =====================================================

    query_gis = (
        gis[
            gis["query"]
            ==
            query_id
        ]
        .copy()
        .sort_values(
            "gis_score",
            ascending=False
        )
    )


    gis_candidates = (
        query_gis[
            "building_id"
        ]
        .astype(str)
        .tolist()
    )


    if len(
        gis_candidates
    ) > 0:

        gis_top1 = (
            gis_candidates[0]
        )

    else:

        gis_top1 = (
            "NO_BUILDING"
        )


    # =====================================================
    # FUSION
    # =====================================================

    query_fusion = (
        fusion[
            fusion["query"]
            ==
            query_id
        ]
        .copy()
        .sort_values(
            "rank"
        )
    )


    fusion_candidates = (
        query_fusion[
            "building_id"
        ]
        .astype(str)
        .tolist()
    )


    if len(
        fusion_candidates
    ) > 0:

        fusion_top1 = (
            fusion_candidates[0]
        )

    else:

        fusion_top1 = (
            "NO_BUILDING"
        )


    fusion_top3 = (
        fusion_candidates[:3]
    )


    # =====================================================
    # GIS TOP-1
    # =====================================================

    gis_top1_correct = int(
        gis_top1
        ==
        true_building
    )


    # =====================================================
    # FUSION TOP-1
    # =====================================================

    fusion_top1_correct = int(
        fusion_top1
        ==
        true_building
    )


    # =====================================================
    # FUSION TOP-3
    # =====================================================

    if (
        true_building
        ==
        "NO_BUILDING"
    ):

        fusion_top3_correct = int(
            len(
                fusion_candidates
            )
            ==
            0
        )

    else:

        fusion_top3_correct = int(
            true_building
            in
            fusion_top3
        )


    # =====================================================
    # GIS CANDIDATE RECALL
    #
    # NO_BUILDING est évalué séparément.
    # =====================================================

    if (
        true_building
        ==
        "NO_BUILDING"
    ):

        candidate_recall = None

        correct_no_building = int(
            len(
                gis_candidates
            )
            ==
            0
        )

    else:

        candidate_recall = int(
            true_building
            in
            gis_candidates
        )

        correct_no_building = None


    # =====================================================
    # SCORES DU TOP-1 FUSION
    # =====================================================

    if not query_fusion.empty:

        top1_row = (
            query_fusion.iloc[0]
        )


        final_score = float(
            top1_row[
                "final_score"
            ]
        )


        gis_score = float(
            top1_row[
                "gis_score"
            ]
        )


        vision_score = float(
            top1_row[
                "vision_score"
            ]
        )


        inliers = int(
            top1_row[
                "inliers"
            ]
        )


    else:

        final_score = 0.0

        gis_score = 0.0

        vision_score = 0.0

        inliers = 0


    # =====================================================
    # SAUVEGARDE QUERY
    # =====================================================

    rows.append({

        "query_id":
            query_id,

        "true_building_id":
            true_building,

        "gis_top1":
            gis_top1,

        "fusion_top1":
            fusion_top1,

        "fusion_top3":
            "|".join(
                fusion_top3
            ),

        "gis_candidate_count":
            len(
                gis_candidates
            ),

        "gis_candidate_recall":
            candidate_recall,

        "gis_top1_correct":
            gis_top1_correct,

        "fusion_top1_correct":
            fusion_top1_correct,

        "fusion_top3_correct":
            fusion_top3_correct,

        "correct_no_building":
            correct_no_building,

        "top1_gis_score":
            gis_score,

        "top1_vision_score":
            vision_score,

        "top1_final_score":
            final_score,

        "top1_inliers":
            inliers
    })


# =========================================================
# 7. DATAFRAME DÉTAILLÉ
# =========================================================

details = pd.DataFrame(
    rows
)


details.to_csv(
    OUTPUT_DETAILS_PATH,
    index=False
)


# =========================================================
# 8. ACCURACY GIS TOP-1
# =========================================================

gis_top1_accuracy = (
    details[
        "gis_top1_correct"
    ]
    .mean()
)


# =========================================================
# 9. ACCURACY FUSION TOP-1
# =========================================================

fusion_top1_accuracy = (
    details[
        "fusion_top1_correct"
    ]
    .mean()
)


# =========================================================
# 10. ACCURACY FUSION TOP-3
# =========================================================

fusion_top3_accuracy = (
    details[
        "fusion_top3_correct"
    ]
    .mean()
)


# =========================================================
# 11. GIS CANDIDATE RECALL
# =========================================================

building_queries = (
    details[
        details[
            "true_building_id"
        ]
        !=
        "NO_BUILDING"
    ]
)


if not building_queries.empty:

    gis_candidate_recall = (

        building_queries[
            "gis_candidate_recall"
        ]
        .astype(float)
        .mean()
    )

else:

    gis_candidate_recall = float(
        "nan"
    )


# =========================================================
# 12. NO_BUILDING ACCURACY
# =========================================================

no_building_queries = (
    details[
        details[
            "true_building_id"
        ]
        ==
        "NO_BUILDING"
    ]
)


if not no_building_queries.empty:

    no_building_accuracy = (

        no_building_queries[
            "correct_no_building"
        ]
        .astype(float)
        .mean()
    )

else:

    no_building_accuracy = float(
        "nan"
    )


# =========================================================
# 13. COMPTER LES ERREURS
# =========================================================

gis_errors = int(
    (
        details[
            "gis_top1_correct"
        ]
        ==
        0
    ).sum()
)


fusion_errors = int(
    (
        details[
            "fusion_top1_correct"
        ]
        ==
        0
    ).sum()
)


# =========================================================
# 14. COMPARAISON GIS VS FUSION
# =========================================================

fusion_improvements = (

    details[
        (
            details[
                "gis_top1_correct"
            ]
            ==
            0
        )
        &
        (
            details[
                "fusion_top1_correct"
            ]
            ==
            1
        )
    ]

)


fusion_degradations = (

    details[
        (
            details[
                "gis_top1_correct"
            ]
            ==
            1
        )
        &
        (
            details[
                "fusion_top1_correct"
            ]
            ==
            0
        )
    ]

)


# =========================================================
# 15. RÉSUMÉ
# =========================================================

summary = pd.DataFrame(

    [
        {
            "metric":
                "verified_queries",

            "value":
                len(
                    details
                )
        },

        {
            "metric":
                "gis_top1_accuracy",

            "value":
                gis_top1_accuracy
        },

        {
            "metric":
                "fusion_top1_accuracy",

            "value":
                fusion_top1_accuracy
        },

        {
            "metric":
                "fusion_top3_accuracy",

            "value":
                fusion_top3_accuracy
        },

        {
            "metric":
                "gis_candidate_recall",

            "value":
                gis_candidate_recall
        },

        {
            "metric":
                "no_building_accuracy",

            "value":
                no_building_accuracy
        },

        {
            "metric":
                "gis_top1_errors",

            "value":
                gis_errors
        },

        {
            "metric":
                "fusion_top1_errors",

            "value":
                fusion_errors
        },

        {
            "metric":
                "fusion_improvements",

            "value":
                len(
                    fusion_improvements
                )
        },

        {
            "metric":
                "fusion_degradations",

            "value":
                len(
                    fusion_degradations
                )
        }
    ]

)


summary.to_csv(
    OUTPUT_SUMMARY_PATH,
    index=False
)


# =========================================================
# 16. AFFICHAGE
# =========================================================

print(
    "\n======================================"
)

print(
    "RÉSULTATS"
)

print(
    "======================================"
)


print(
    f"GIS Top-1 Accuracy : "
    f"{gis_top1_accuracy:.4f} "
    f"({gis_top1_accuracy * 100:.2f}%)"
)


print(
    f"Fusion Top-1 Accuracy : "
    f"{fusion_top1_accuracy:.4f} "
    f"({fusion_top1_accuracy * 100:.2f}%)"
)


print(
    f"Fusion Top-3 Accuracy : "
    f"{fusion_top3_accuracy:.4f} "
    f"({fusion_top3_accuracy * 100:.2f}%)"
)


if pd.notna(
    gis_candidate_recall
):

    print(
        f"GIS Candidate Recall : "
        f"{gis_candidate_recall:.4f} "
        f"({gis_candidate_recall * 100:.2f}%)"
    )


if pd.notna(
    no_building_accuracy
):

    print(
        f"NO_BUILDING Accuracy : "
        f"{no_building_accuracy:.4f} "
        f"({no_building_accuracy * 100:.2f}%)"
    )


print(
    "\nGIS Top-1 erreurs :",
    gis_errors
)


print(
    "Fusion Top-1 erreurs :",
    fusion_errors
)


print(
    "Cas corrigés par la fusion :",
    len(
        fusion_improvements
    )
)


print(
    "Cas dégradés par la fusion :",
    len(
        fusion_degradations
    )
)


# =========================================================
# 17. AFFICHER LES ERREURS FUSION
# =========================================================

fusion_wrong = (

    details[
        details[
            "fusion_top1_correct"
        ]
        ==
        0
    ]

)


print(
    "\n======================================"
)

print(
    "ERREURS FUSION"
)

print(
    "======================================"
)


if fusion_wrong.empty:

    print(
        "Aucune erreur sur les ground truth vérifiés."
    )

else:

    print(

        fusion_wrong[
            [
                "query_id",
                "true_building_id",
                "gis_top1",
                "fusion_top1",
                "fusion_top3",
                "top1_gis_score",
                "top1_vision_score",
                "top1_final_score",
                "top1_inliers"
            ]
        ]
        .to_string(
            index=False
        )
    )


# =========================================================
# 18. CAS OÙ LA FUSION AMÉLIORE LE GIS
# =========================================================

print(
    "\n======================================"
)

print(
    "CAS CORRIGÉS PAR LA FUSION"
)

print(
    "======================================"
)


if fusion_improvements.empty:

    print(
        "Aucun cas."
    )

else:

    print(

        fusion_improvements[
            [
                "query_id",
                "true_building_id",
                "gis_top1",
                "fusion_top1"
            ]
        ]
        .to_string(
            index=False
        )
    )


# =========================================================
# 19. CAS OÙ LA FUSION DÉGRADE LE GIS
# =========================================================

print(
    "\n======================================"
)

print(
    "CAS DÉGRADÉS PAR LA FUSION"
)

print(
    "======================================"
)


if fusion_degradations.empty:

    print(
        "Aucun cas."
    )

else:

    print(

        fusion_degradations[
            [
                "query_id",
                "true_building_id",
                "gis_top1",
                "fusion_top1"
            ]
        ]
        .to_string(
            index=False
        )
    )


# =========================================================
# 20. FICHIERS
# =========================================================

print(
    "\n======================================"
)

print(
    "FICHIERS GÉNÉRÉS"
)

print(
    "======================================"
)


print(
    OUTPUT_DETAILS_PATH
)

print(
    OUTPUT_SUMMARY_PATH
)


print(
    "\nÉvaluation terminée."
)
