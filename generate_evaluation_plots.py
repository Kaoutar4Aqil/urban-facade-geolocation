import os
import sys
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

DETAILS_PATH = (
    "data/processed/"
    "evaluation_subset_v1_details.csv"
)

SUMMARY_PATH = (
    "data/processed/"
    "evaluation_subset_v1_summary.csv"
)

OUTPUT_DIR = (
    "data/processed/"
    "evaluation_plots"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# VÉRIFICATION DES FICHIERS
# ============================================================

print()
print("======================================")
print("GÉNÉRATION DES GRAPHIQUES")
print("======================================")

missing_files = []

for path in [
    DETAILS_PATH,
    SUMMARY_PATH
]:

    if not os.path.exists(path):
        missing_files.append(path)


if missing_files:

    print()
    print(
        "Les fichiers d'évaluation "
        "ne sont pas disponibles."
    )

    for path in missing_files:
        print(
            "[ABSENT]",
            path
        )

    print()
    print(
        "Lance d'abord :"
    )

    print(
        "python evaluate_subset_v1_final.py"
    )

    sys.exit(0)


# ============================================================
# CHARGEMENT
# ============================================================

details = pd.read_csv(
    DETAILS_PATH
)

summary = pd.read_csv(
    SUMMARY_PATH
)


print(
    "Nombre de queries évaluées :",
    len(details)
)


if len(details) == 0:

    print(
        "Aucune query évaluée."
    )

    sys.exit(0)


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def find_column(df, candidates):

    for col in candidates:

        if col in df.columns:
            return col

    return None


def to_numeric(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def save_plot(filename):

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "[OK]",
        path
    )


# ============================================================
# COLONNES PRINCIPALES
# ============================================================

gt_col = find_column(
    details,
    [
        "true_building_id",
        "ground_truth",
        "gt",
    ]
)

gis_top1_col = find_column(
    details,
    [
        "gis_top1",
    ]
)

fusion_top1_col = find_column(
    details,
    [
        "fusion_top1",
    ]
)

fusion_top3_col = find_column(
    details,
    [
        "fusion_top3",
    ]
)

gis_score_col = find_column(
    details,
    [
        "top1_gis_score",
        "gis_score",
    ]
)

vision_score_col = find_column(
    details,
    [
        "top1_vision_score",
        "vision_score",
    ]
)

final_score_col = find_column(
    details,
    [
        "top1_final_score",
        "final_score",
    ]
)

inliers_col = find_column(
    details,
    [
        "top1_inliers",
        "inliers",
    ]
)


# ============================================================
# INDICATEURS OFFICIELS
# ============================================================

# GIS Top-1
if "gis_top1_correct" in details.columns:

    details["gis_correct_calc"] = (
        pd.to_numeric(
            details["gis_top1_correct"],
            errors="coerce"
        )
        .fillna(0)
        .astype(bool)
    )

elif (
    gt_col is not None
    and gis_top1_col is not None
):

    details["gis_correct_calc"] = (
        details[gt_col].astype(str)
        ==
        details[gis_top1_col].astype(str)
    )

else:

    details["gis_correct_calc"] = False


# Fusion Top-1
if "fusion_top1_correct" in details.columns:

    details["fusion_correct_calc"] = (
        pd.to_numeric(
            details["fusion_top1_correct"],
            errors="coerce"
        )
        .fillna(0)
        .astype(bool)
    )

elif (
    gt_col is not None
    and fusion_top1_col is not None
):

    details["fusion_correct_calc"] = (
        details[gt_col].astype(str)
        ==
        details[fusion_top1_col].astype(str)
    )

else:

    details["fusion_correct_calc"] = False


# Fusion Top-3
if "fusion_top3_correct" in details.columns:

    details["fusion_top3_correct_calc"] = (
        pd.to_numeric(
            details["fusion_top3_correct"],
            errors="coerce"
        )
        .fillna(0)
        .astype(bool)
    )

elif (
    gt_col is not None
    and fusion_top3_col is not None
):

    def top3_contains_truth(row):

        truth = str(
            row[gt_col]
        )

        top3 = str(
            row[fusion_top3_col]
        )

        predictions = [
            x.strip()
            for x in top3.split("|")
            if x.strip()
        ]

        return truth in predictions


    details["fusion_top3_correct_calc"] = (
        details.apply(
            top3_contains_truth,
            axis=1
        )
    )

else:

    details["fusion_top3_correct_calc"] = False


# ============================================================
# MÉTRIQUES PRINCIPALES
# ============================================================

total = len(details)


gis_accuracy = (
    details[
        "gis_correct_calc"
    ].mean()
)


fusion_accuracy = (
    details[
        "fusion_correct_calc"
    ].mean()
)


fusion_top3_accuracy = (
    details[
        "fusion_top3_correct_calc"
    ].mean()
)


# ============================================================
# GIS CANDIDATE RECALL OFFICIEL
# ============================================================

candidate_recall = None


if "gis_candidate_recall" in details.columns:

    candidate_values = (
        pd.to_numeric(
            details[
                "gis_candidate_recall"
            ],
            errors="coerce"
        )
        .dropna()
    )

    if len(candidate_values) > 0:

        candidate_recall = (
            candidate_values.mean()
        )


# ============================================================
# NO_BUILDING ACCURACY
# ============================================================

no_building_accuracy = None


if "correct_no_building" in details.columns:

    if gt_col is not None:

        no_building_mask = (
            details[gt_col]
            .astype(str)
            .eq("NO_BUILDING")
        )

        no_building_rows = details[
            no_building_mask
        ]

        if len(no_building_rows) > 0:

            no_building_accuracy = (
                pd.to_numeric(
                    no_building_rows[
                        "correct_no_building"
                    ],
                    errors="coerce"
                )
                .dropna()
                .mean()
            )


# ============================================================
# 1. ACCURACY COMPARISON
# ============================================================

plt.figure(
    figsize=(8, 5)
)


methods = [
    "GIS Top-1",
    "Fusion Top-1",
    "Fusion Top-3",
]


values = [
    gis_accuracy * 100,
    fusion_accuracy * 100,
    fusion_top3_accuracy * 100,
]


bars = plt.bar(
    methods,
    values
)


plt.ylabel(
    "Accuracy (%)"
)


plt.title(
    "Accuracy Comparison"
)


plt.ylim(
    0,
    100
)


plt.grid(
    axis="y",
    alpha=0.25
)


for bar, value in zip(
    bars,
    values
):

    plt.text(
        bar.get_x()
        +
        bar.get_width() / 2,

        min(
            value + 2,
            98
        ),

        f"{value:.2f}%",

        ha="center",
        va="bottom"
    )


save_plot(
    "accuracy_comparison.png"
)


# ============================================================
# 2. GIS CANDIDATE RECALL
# ============================================================

if candidate_recall is not None:

    plt.figure(
        figsize=(6, 5)
    )


    values = [
        candidate_recall * 100,
        (
            1
            -
            candidate_recall
        ) * 100,
    ]


    labels = [
        "GT in GIS\ncandidates",
        "GT missing from\nGIS candidates",
    ]


    bars = plt.bar(
        labels,
        values
    )


    plt.ylabel(
        "Percentage (%)"
    )


    plt.title(
        "GIS Candidate Recall"
    )


    plt.ylim(
        0,
        100
    )


    plt.grid(
        axis="y",
        alpha=0.25
    )


    for bar, value in zip(
        bars,
        values
    ):

        plt.text(
            bar.get_x()
            +
            bar.get_width() / 2,

            min(
                value + 2,
                98
            ),

            f"{value:.2f}%",

            ha="center",
            va="bottom"
        )


    save_plot(
        "gis_candidate_recall.png"
    )


# ============================================================
# 3. GIS CORRECT VS WRONG
# ============================================================

gis_correct = int(
    details[
        "gis_correct_calc"
    ].sum()
)


gis_wrong = (
    total
    -
    gis_correct
)


plt.figure(
    figsize=(6, 5)
)


bars = plt.bar(
    [
        "Correct",
        "Wrong",
    ],
    [
        gis_correct,
        gis_wrong,
    ]
)


plt.ylabel(
    "Number of queries"
)


plt.title(
    "GIS Top-1: Correct vs Wrong"
)


plt.grid(
    axis="y",
    alpha=0.25
)


for bar, value in zip(
    bars,
    [
        gis_correct,
        gis_wrong,
    ]
):

    plt.text(
        bar.get_x()
        +
        bar.get_width() / 2,

        value + 0.2,

        str(value),

        ha="center",
        va="bottom"
    )


save_plot(
    "gis_correct_vs_wrong.png"
)


# ============================================================
# 4. FUSION CORRECT VS WRONG
# ============================================================

fusion_correct = int(
    details[
        "fusion_correct_calc"
    ].sum()
)


fusion_wrong = (
    total
    -
    fusion_correct
)


plt.figure(
    figsize=(6, 5)
)


bars = plt.bar(
    [
        "Correct",
        "Wrong",
    ],
    [
        fusion_correct,
        fusion_wrong,
    ]
)


plt.ylabel(
    "Number of queries"
)


plt.title(
    "Fusion Top-1: Correct vs Wrong"
)


plt.grid(
    axis="y",
    alpha=0.25
)


for bar, value in zip(
    bars,
    [
        fusion_correct,
        fusion_wrong,
    ]
):

    plt.text(
        bar.get_x()
        +
        bar.get_width() / 2,

        value + 0.2,

        str(value),

        ha="center",
        va="bottom"
    )


save_plot(
    "fusion_correct_vs_wrong.png"
)


# ============================================================
# 5. FUSION SCORE DISTRIBUTION
# ============================================================

if final_score_col is not None:

    scores = (
        to_numeric(
            details[
                final_score_col
            ]
        )
        .dropna()
    )


    if len(scores) > 0:

        plt.figure(
            figsize=(8, 5)
        )


        plt.hist(
            scores,
            bins=10
        )


        plt.xlabel(
            "Fusion final score"
        )


        plt.ylabel(
            "Number of queries"
        )


        plt.title(
            "Fusion Score Distribution"
        )


        plt.grid(
            axis="y",
            alpha=0.25
        )


        save_plot(
            "fusion_score_distribution.png"
        )


# ============================================================
# 6. RANSAC INLIERS : CORRECT VS WRONG
# ============================================================

if inliers_col is not None:

    details[
        "_inliers_numeric"
    ] = to_numeric(
        details[
            inliers_col
        ]
    )


    correct_inliers = (
        details.loc[
            details[
                "fusion_correct_calc"
            ],
            "_inliers_numeric"
        ]
        .dropna()
        .tolist()
    )


    wrong_inliers = (
        details.loc[
            ~details[
                "fusion_correct_calc"
            ],
            "_inliers_numeric"
        ]
        .dropna()
        .tolist()
    )


    box_data = []
    box_labels = []


    if len(correct_inliers) > 0:

        box_data.append(
            correct_inliers
        )

        box_labels.append(
            "Correct"
        )


    if len(wrong_inliers) > 0:

        box_data.append(
            wrong_inliers
        )

        box_labels.append(
            "Wrong"
        )


    if box_data:

        plt.figure(
            figsize=(7, 5)
        )


        plt.boxplot(
            box_data,
            tick_labels=box_labels
        )


        plt.ylabel(
            "Number of RANSAC inliers"
        )


        plt.title(
            "RANSAC Inliers: "
            "Correct vs Wrong Fusion Predictions"
        )


        plt.grid(
            axis="y",
            alpha=0.25
        )


        save_plot(
            "fusion_inliers_boxplot.png"
        )


# ============================================================
# 7. GIS SCORE : CORRECT VS WRONG
# ============================================================

if gis_score_col is not None:

    details[
        "_gis_score_numeric"
    ] = to_numeric(
        details[
            gis_score_col
        ]
    )


    correct_scores = (
        details.loc[
            details[
                "gis_correct_calc"
            ],
            "_gis_score_numeric"
        ]
        .dropna()
        .tolist()
    )


    wrong_scores = (
        details.loc[
            ~details[
                "gis_correct_calc"
            ],
            "_gis_score_numeric"
        ]
        .dropna()
        .tolist()
    )


    box_data = []
    box_labels = []


    if len(correct_scores) > 0:

        box_data.append(
            correct_scores
        )

        box_labels.append(
            "Correct"
        )


    if len(wrong_scores) > 0:

        box_data.append(
            wrong_scores
        )

        box_labels.append(
            "Wrong"
        )


    if box_data:

        plt.figure(
            figsize=(7, 5)
        )


        plt.boxplot(
            box_data,
            tick_labels=box_labels
        )


        plt.ylabel(
            "GIS score"
        )


        plt.title(
            "GIS Scores: "
            "Correct vs Wrong Predictions"
        )


        plt.grid(
            axis="y",
            alpha=0.25
        )


        save_plot(
            "gis_score_boxplot.png"
        )


# ============================================================
# 8. VISION SCORE : CORRECT VS WRONG
# ============================================================

if vision_score_col is not None:

    details[
        "_vision_score_numeric"
    ] = to_numeric(
        details[
            vision_score_col
        ]
    )


    correct_scores = (
        details.loc[
            details[
                "fusion_correct_calc"
            ],
            "_vision_score_numeric"
        ]
        .dropna()
        .tolist()
    )


    wrong_scores = (
        details.loc[
            ~details[
                "fusion_correct_calc"
            ],
            "_vision_score_numeric"
        ]
        .dropna()
        .tolist()
    )


    box_data = []
    box_labels = []


    if len(correct_scores) > 0:

        box_data.append(
            correct_scores
        )

        box_labels.append(
            "Correct"
        )


    if len(wrong_scores) > 0:

        box_data.append(
            wrong_scores
        )

        box_labels.append(
            "Wrong"
        )


    if box_data:

        plt.figure(
            figsize=(7, 5)
        )


        plt.boxplot(
            box_data,
            tick_labels=box_labels
        )


        plt.ylabel(
            "Vision score"
        )


        plt.title(
            "Vision Scores: "
            "Correct vs Wrong Fusion Predictions"
        )


        plt.grid(
            axis="y",
            alpha=0.25
        )


        save_plot(
            "vision_score_boxplot.png"
        )


# ============================================================
# 9. GIS SCORE VS FUSION SCORE
# ============================================================

if (
    gis_score_col is not None
    and
    final_score_col is not None
):

    gis_values = to_numeric(
        details[
            gis_score_col
        ]
    )


    fusion_values = to_numeric(
        details[
            final_score_col
        ]
    )


    valid = (
        gis_values.notna()
        &
        fusion_values.notna()
    )


    if valid.any():

        plt.figure(
            figsize=(7, 6)
        )


        plt.scatter(
            gis_values[
                valid
            ],
            fusion_values[
                valid
            ],
            alpha=0.75
        )


        plt.xlabel(
            "GIS score"
        )


        plt.ylabel(
            "Fusion final score"
        )


        plt.title(
            "GIS Score vs Fusion Score"
        )


        plt.grid(
            alpha=0.25
        )


        save_plot(
            "gis_vs_fusion_score.png"
        )


# ============================================================
# 10. ERREURS FUSION
# ============================================================

fusion_errors = details[
    ~details[
        "fusion_correct_calc"
    ]
].copy()


fusion_errors_path = os.path.join(
    OUTPUT_DIR,
    "fusion_errors.csv"
)


fusion_errors.to_csv(
    fusion_errors_path,
    index=False
)


print(
    "[OK]",
    fusion_errors_path
)


# ============================================================
# 11. CAS CORRIGÉS PAR LA FUSION
# ============================================================

fusion_improvements = details[
    (
        ~details[
            "gis_correct_calc"
        ]
    )
    &
    (
        details[
            "fusion_correct_calc"
        ]
    )
].copy()


improvements_path = os.path.join(
    OUTPUT_DIR,
    "fusion_improvements.csv"
)


fusion_improvements.to_csv(
    improvements_path,
    index=False
)


print(
    "[OK]",
    improvements_path
)


# ============================================================
# 12. CAS DÉGRADÉS PAR LA FUSION
# ============================================================

fusion_degradations = details[
    (
        details[
            "gis_correct_calc"
        ]
    )
    &
    (
        ~details[
            "fusion_correct_calc"
        ]
    )
].copy()


degradations_path = os.path.join(
    OUTPUT_DIR,
    "fusion_degradations.csv"
)


fusion_degradations.to_csv(
    degradations_path,
    index=False
)


print(
    "[OK]",
    degradations_path
)


# ============================================================
# RÉSUMÉ FINAL
# ============================================================

print()
print("======================================")
print("RÉSUMÉ")
print("======================================")


print(
    f"GIS Top-1 Accuracy : "
    f"{gis_accuracy:.4f} "
    f"({gis_accuracy * 100:.2f}%)"
)


print(
    f"Fusion Top-1 Accuracy : "
    f"{fusion_accuracy:.4f} "
    f"({fusion_accuracy * 100:.2f}%)"
)


print(
    f"Fusion Top-3 Accuracy : "
    f"{fusion_top3_accuracy:.4f} "
    f"({fusion_top3_accuracy * 100:.2f}%)"
)


if candidate_recall is not None:

    print(
        f"GIS Candidate Recall : "
        f"{candidate_recall:.4f} "
        f"({candidate_recall * 100:.2f}%)"
    )


if no_building_accuracy is not None:

    print(
        f"NO_BUILDING Accuracy : "
        f"{no_building_accuracy:.4f} "
        f"({no_building_accuracy * 100:.2f}%)"
    )


print()

print(
    "Erreurs GIS :",
    gis_wrong
)

print(
    "Erreurs Fusion :",
    fusion_wrong
)

print(
    "Cas corrigés par fusion :",
    len(
        fusion_improvements
    )
)

print(
    "Cas dégradés par fusion :",
    len(
        fusion_degradations
    )
)


# ============================================================
# FIN
# ============================================================

print()
print("======================================")
print("GRAPHIQUES TERMINÉS")
print("======================================")


print(
    "Dossier :",
    OUTPUT_DIR
)


print()
print(
    "Tous les graphiques et fichiers "
    "d'analyse ont été générés."
)
