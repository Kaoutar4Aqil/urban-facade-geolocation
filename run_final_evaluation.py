import os
import sys
import subprocess
import pandas as pd


# =========================================================
# 1. CHEMINS
# =========================================================

GROUND_TRUTH_PATH = (
    "data/metadata/"
    "ground_truth_subset_v1.csv"
)

QUERY_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)

GIS_PATH = (
    "data/processed/"
    "batch_gis_candidates_subset_v1.csv"
)

FUSION_PATH = (
    "data/processed/"
    "batch_final_predictions_subset_v1_clean.csv"
)

EVALUATION_SCRIPT = (
    "evaluate_subset_v1_final.py"
)

PLOTS_SCRIPT = (
    "generate_evaluation_plots.py"
)

DETAILS_PATH = (
    "data/processed/"
    "evaluation_subset_v1_details.csv"
)

SUMMARY_PATH = (
    "data/processed/"
    "evaluation_subset_v1_summary.csv"
)

PLOTS_DIR = (
    "data/processed/"
    "evaluation_plots"
)


# =========================================================
# 2. FONCTION AFFICHAGE
# =========================================================

def separator():

    print(
        "\n======================================"
    )


# =========================================================
# 3. VÉRIFICATION DES FICHIERS PRINCIPAUX
# =========================================================

separator()

print(
    "VÉRIFICATION DES FICHIERS"
)

separator()


required_files = {

    "Ground truth":
        GROUND_TRUTH_PATH,

    "Queries":
        QUERY_PATH,

    "GIS candidates":
        GIS_PATH,

    "Fusion predictions":
        FUSION_PATH,

    "Evaluation script":
        EVALUATION_SCRIPT,

    "Plots script":
        PLOTS_SCRIPT
}


missing_files = []


for name, path in required_files.items():

    if os.path.exists(
        path
    ):

        print(
            "[OK]",
            name,
            "->",
            path
        )

    else:

        print(
            "[MISSING]",
            name,
            "->",
            path
        )

        missing_files.append(
            path
        )


if missing_files:

    separator()

    print(
        "ERREUR"
    )

    separator()

    print(
        "Certains fichiers nécessaires "
        "sont absents."
    )

    print(
        "Impossible de lancer "
        "l'évaluation finale."
    )

    sys.exit(1)


# =========================================================
# 4. CHARGER LES QUERIES
# =========================================================

queries = pd.read_csv(
    QUERY_PATH
)


queries["image_id"] = (
    queries["image_id"]
    .astype(str)
)


total_queries = len(
    queries
)


print(
    "\nNombre de queries :",
    total_queries
)


# =========================================================
# 5. CHARGER LE GROUND TRUTH
# =========================================================

ground_truth = pd.read_csv(
    GROUND_TRUTH_PATH
)


ground_truth["query_id"] = (
    ground_truth["query_id"]
    .astype(str)
)


ground_truth["true_building_id"] = (
    ground_truth[
        "true_building_id"
    ]
    .fillna("")
    .astype(str)
    .str.strip()
)


ground_truth["status"] = (
    ground_truth[
        "status"
    ]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)


print(
    "Nombre de lignes ground truth :",
    len(
        ground_truth
    )
)


# =========================================================
# 6. VÉRIFIER LE NOMBRE DE LIGNES
# =========================================================

if (
    len(
        ground_truth
    )
    !=
    total_queries
):

    separator()

    print(
        "ERREUR GROUND TRUTH"
    )

    separator()

    print(
        "Nombre de queries attendu :",
        total_queries
    )

    print(
        "Nombre de ground truth trouvé :",
        len(
            ground_truth
        )
    )

    print(
        "Le fichier ground truth doit contenir "
        "exactement une ligne par query."
    )

    sys.exit(1)


# =========================================================
# 7. VÉRIFIER LES DOUBLONS
# =========================================================

duplicates = (

    ground_truth[
        ground_truth[
            "query_id"
        ]
        .duplicated(
            keep=False
        )
    ]

)


if not duplicates.empty:

    separator()

    print(
        "ERREUR : QUERY_ID DUPLIQUÉS"
    )

    separator()

    print(

        duplicates[
            [
                "query_id",
                "true_building_id",
                "status"
            ]
        ]
        .to_string(
            index=False
        )
    )

    sys.exit(1)


# =========================================================
# 8. VÉRIFIER QUE TOUTES LES QUERIES SONT PRÉSENTES
# =========================================================

query_ids = set(
    queries[
        "image_id"
    ]
)


gt_ids = set(
    ground_truth[
        "query_id"
    ]
)


missing_gt = sorted(
    query_ids
    -
    gt_ids
)


extra_gt = sorted(
    gt_ids
    -
    query_ids
)


if missing_gt:

    separator()

    print(
        "QUERIES ABSENTES DU GROUND TRUTH"
    )

    separator()

    for query_id in missing_gt:

        print(
            "-",
            query_id
        )


if extra_gt:

    separator()

    print(
        "QUERIES INCONNUES DANS LE GROUND TRUTH"
    )

    separator()

    for query_id in extra_gt:

        print(
            "-",
            query_id
        )


if (
    missing_gt
    or
    extra_gt
):

    sys.exit(1)


# =========================================================
# 9. VÉRIFIER LES STATUTS
# =========================================================

verified_mask = (

    ground_truth[
        "status"
    ]
    ==
    "verified"
)


pending_mask = (

    ground_truth[
        "status"
    ]
    !=
    "verified"
)


empty_gt_mask = (

    ground_truth[
        "true_building_id"
    ]
    ==
    ""
)


verified_count = int(
    verified_mask.sum()
)


pending_count = int(
    pending_mask.sum()
)


empty_count = int(
    empty_gt_mask.sum()
)


separator()

print(
    "ÉTAT DU GROUND TRUTH"
)

separator()


print(
    "Total :",
    len(
        ground_truth
    )
)


print(
    "Verified :",
    verified_count
)


print(
    "Non verified :",
    pending_count
)


print(
    "true_building_id vides :",
    empty_count
)


# =========================================================
# 10. REFUSER SI GROUND TRUTH INCOMPLET
# =========================================================

incomplete = (

    ground_truth[
        pending_mask
        |
        empty_gt_mask
    ]
    .copy()
)


if not incomplete.empty:

    separator()

    print(
        "GROUND TRUTH INCOMPLET"
    )

    separator()


    print(
        "L'évaluation finale ne sera pas lancée."
    )


    print(
        "\nQueries restant à annoter :"
    )


    print(

        incomplete[
            [
                "query_id",
                "true_building_id",
                "status"
            ]
        ]
        .to_string(
            index=False
        )
    )


    print(
        "\nIl reste",
        len(
            incomplete
        ),
        "query(s) à vérifier."
    )


    print(
        "\nComplète :"
    )


    print(
        GROUND_TRUTH_PATH
    )


    print(
        "\nPuis relance :"
    )


    print(
        "python run_final_evaluation.py"
    )


    sys.exit(0)


# =========================================================
# 11. GROUND TRUTH COMPLET
# =========================================================

separator()

print(
    "GROUND TRUTH COMPLET"
)

separator()


print(
    "Toutes les queries sont annotées."
)


print(
    "Lancement de l'évaluation finale..."
)


# =========================================================
# 12. SUPPRIMER ANCIENS RÉSULTATS
#     POUR ÉVITER DES FICHIERS OBSOLÈTES
# =========================================================

for path in [

    DETAILS_PATH,
    SUMMARY_PATH

]:

    if os.path.exists(
        path
    ):

        os.remove(
            path
        )

        print(
            "[REMOVED OLD]",
            path
        )


# =========================================================
# 13. LANCER L'ÉVALUATION
# =========================================================

separator()

print(
    "ÉTAPE 1/2 : ÉVALUATION"
)

separator()


evaluation_result = subprocess.run(

    [
        sys.executable,
        EVALUATION_SCRIPT
    ],

    check=False
)


if (
    evaluation_result.returncode
    !=
    0
):

    separator()

    print(
        "ERREUR DURANT L'ÉVALUATION"
    )

    separator()

    print(
        "Code retour :",
        evaluation_result.returncode
    )

    sys.exit(
        evaluation_result.returncode
    )


# =========================================================
# 14. VÉRIFIER LES SORTIES D'ÉVALUATION
# =========================================================

if not os.path.exists(
    DETAILS_PATH
):

    print(
        "[ERROR] Fichier manquant :",
        DETAILS_PATH
    )

    sys.exit(1)


if not os.path.exists(
    SUMMARY_PATH
):

    print(
        "[ERROR] Fichier manquant :",
        SUMMARY_PATH
    )

    sys.exit(1)


print(
    "\n[OK] Évaluation terminée."
)


# =========================================================
# 15. LANCER LES GRAPHIQUES
# =========================================================

separator()

print(
    "ÉTAPE 2/2 : GRAPHIQUES"
)

separator()


plots_result = subprocess.run(

    [
        sys.executable,
        PLOTS_SCRIPT
    ],

    check=False
)


if (
    plots_result.returncode
    !=
    0
):

    separator()

    print(
        "ERREUR DURANT LA GÉNÉRATION "
        "DES GRAPHIQUES"
    )

    separator()

    print(
        "Code retour :",
        plots_result.returncode
    )

    sys.exit(
        plots_result.returncode
    )


# =========================================================
# 16. CHARGER LE RÉSUMÉ
# =========================================================

summary = pd.read_csv(
    SUMMARY_PATH
)


separator()

print(
    "RÉSUMÉ FINAL"
)

separator()


for _, row in summary.iterrows():

    metric = str(
        row[
            "metric"
        ]
    )


    value = row[
        "value"
    ]


    if metric in [

        "gis_top1_accuracy",
        "fusion_top1_accuracy",
        "fusion_top3_accuracy",
        "gis_candidate_recall",
        "no_building_accuracy"

    ]:

        try:

            numeric_value = float(
                value
            )


            if pd.notna(
                numeric_value
            ):

                print(
                    f"{metric} : "
                    f"{numeric_value:.4f} "
                    f"({numeric_value * 100:.2f}%)"
                )

            else:

                print(
                    f"{metric} : N/A"
                )

        except (
            TypeError,
            ValueError
        ):

            print(
                f"{metric} :",
                value
            )

    else:

        print(
            f"{metric} :",
            value
        )


# =========================================================
# 17. LISTER LES GRAPHIQUES
# =========================================================

separator()

print(
    "GRAPHIQUES"
)

separator()


if os.path.isdir(
    PLOTS_DIR
):

    plot_files = sorted(

        [
            filename

            for filename
            in os.listdir(
                PLOTS_DIR
            )

            if filename.lower().endswith(
                (
                    ".png",
                    ".csv"
                )
            )
        ]
    )


    if plot_files:

        for filename in plot_files:

            print(
                "[OK]",
                os.path.join(
                    PLOTS_DIR,
                    filename
                )
            )

    else:

        print(
            "Aucun fichier trouvé."
        )

else:

    print(
        "Dossier absent :",
        PLOTS_DIR
    )


# =========================================================
# 18. FIN
# =========================================================

separator()

print(
    "PIPELINE D'ÉVALUATION TERMINÉ"
)

separator()


print(
    "Ground truth :",
    GROUND_TRUTH_PATH
)


print(
    "Résultats détaillés :",
    DETAILS_PATH
)


print(
    "Résumé :",
    SUMMARY_PATH
)


print(
    "Graphiques :",
    PLOTS_DIR
)


print(
    "\nSTATUS : OK"
)
