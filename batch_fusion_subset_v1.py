import os
import cv2
import numpy as np
import pandas as pd


# =========================================================
# 1. Chemins
# =========================================================

QUERY_METADATA_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)

QUERY_IMAGE_DIR = (
    "data/raw/"
    "query_subset_v1"
)

GIS_PATH = (
    "data/processed/"
    "batch_gis_candidates_subset_v1.csv"
)

REFERENCE_METADATA_PATH = (
    "data/processed/"
    "reference_pool_subset_v3_clean.csv"
)

REFERENCE_IMAGE_DIR = (
    "data/raw/"
    "reference_pool_subset_v3"
)

OUTPUT_PATH = (
    "data/processed/"
    "batch_final_predictions_subset_v1_clean.csv"
)


# =========================================================
# 2. Paramètres SIFT / matching
# =========================================================

LOWE_RATIO = 0.75

RANSAC_THRESHOLD = 5.0

MIN_GOOD_MATCHES_FOR_HOMOGRAPHY = 4


# =========================================================
# 3. Poids fusion
# =========================================================

VISION_WEIGHT = 0.60

GIS_WEIGHT = 0.40


# =========================================================
# 4. Charger les données
# =========================================================

queries = pd.read_csv(
    QUERY_METADATA_PATH
)

gis = pd.read_csv(
    GIS_PATH
)

references = pd.read_csv(
    REFERENCE_METADATA_PATH
)


queries["image_id"] = (
    queries["image_id"]
    .astype(str)
)

queries["sequence"] = (
    queries["sequence"]
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


references["building_id"] = (
    references["building_id"]
    .astype(str)
)

references["reference_image_id"] = (
    references["reference_image_id"]
    .astype(str)
)

references["sequence"] = (
    references["sequence"]
    .fillna("")
    .astype(str)
)


print(
    "Nombre de queries :",
    len(queries)
)

print(
    "Nombre de couples GIS query-building :",
    len(gis)
)

print(
    "Nombre de références propres :",
    len(references)
)

print(
    "Nombre de bâtiments avec références propres :",
    references["building_id"].nunique()
)


# =========================================================
# 5. Initialisation SIFT
# =========================================================

sift = cv2.SIFT_create()


matcher = cv2.BFMatcher(
    cv2.NORM_L2,
    crossCheck=False
)


# =========================================================
# 6. Fonction lecture image grayscale
# =========================================================

def load_gray_image(
    image_path
):

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        return None

    return image


# =========================================================
# 7. Calcul SIFT
# =========================================================

def compute_sift(
    image
):

    if image is None:
        return None, None


    keypoints, descriptors = (
        sift.detectAndCompute(
            image,
            None
        )
    )


    return (
        keypoints,
        descriptors
    )


# =========================================================
# 8. Matching SIFT + Lowe + RANSAC
# =========================================================

def match_images(
    query_keypoints,
    query_descriptors,
    ref_keypoints,
    ref_descriptors
):

    result = {

        "good_matches": 0,

        "inliers": 0,

        "inlier_ratio": 0.0
    }


    if (
        query_descriptors is None
        or
        ref_descriptors is None
    ):
        return result


    if (
        len(query_descriptors) < 2
        or
        len(ref_descriptors) < 2
    ):
        return result


    try:

        knn_matches = matcher.knnMatch(
            query_descriptors,
            ref_descriptors,
            k=2
        )

    except cv2.error:
        return result


    good_matches = []


    for pair in knn_matches:

        if len(pair) < 2:
            continue


        m, n = pair


        if (
            m.distance
            <
            LOWE_RATIO
            *
            n.distance
        ):

            good_matches.append(
                m
            )


    result[
        "good_matches"
    ] = len(
        good_matches
    )


    if (
        len(good_matches)
        <
        MIN_GOOD_MATCHES_FOR_HOMOGRAPHY
    ):
        return result


    src_points = np.float32(

        [
            query_keypoints[
                match.queryIdx
            ].pt

            for match
            in good_matches
        ]

    ).reshape(
        -1,
        1,
        2
    )


    dst_points = np.float32(

        [
            ref_keypoints[
                match.trainIdx
            ].pt

            for match
            in good_matches
        ]

    ).reshape(
        -1,
        1,
        2
    )


    try:

        homography, mask = (
            cv2.findHomography(
                src_points,
                dst_points,
                cv2.RANSAC,
                RANSAC_THRESHOLD
            )
        )

    except cv2.error:
        return result


    if (
        homography is None
        or
        mask is None
    ):
        return result


    inliers = int(
        mask.ravel().sum()
    )


    inlier_ratio = (
        inliers
        /
        len(good_matches)
        if len(good_matches) > 0
        else 0.0
    )


    result[
        "inliers"
    ] = inliers


    result[
        "inlier_ratio"
    ] = float(
        inlier_ratio
    )


    return result


# =========================================================
# 9. Pré-calcul SIFT références
# =========================================================

print(
    "\n======================================"
)

print(
    "PRÉ-CALCUL SIFT DES RÉFÉRENCES PROPRES"
)

print(
    "======================================"
)


reference_features = {}


for _, ref in references.iterrows():

    building_id = str(
        ref[
            "building_id"
        ]
    )

    reference_id = str(
        ref[
            "reference_image_id"
        ]
    )


    filename = (
        f"{building_id}_"
        f"{reference_id}.jpg"
    )


    image_path = os.path.join(
        REFERENCE_IMAGE_DIR,
        filename
    )


    if not os.path.exists(
        image_path
    ):

        print(
            "[MISSING]",
            image_path
        )

        continue


    image = load_gray_image(
        image_path
    )


    if image is None:

        print(
            "[INVALID IMAGE]",
            image_path
        )

        continue


    keypoints, descriptors = compute_sift(
        image
    )


    if (
        keypoints is None
        or
        descriptors is None
    ):
        continue


    key = (
        building_id,
        reference_id
    )


    reference_features[
        key
    ] = {

        "keypoints":
            keypoints,

        "descriptors":
            descriptors,

        "sequence":
            str(
                ref[
                    "sequence"
                ]
            )
    }


print(
    "Références SIFT disponibles :",
    len(reference_features)
)


# =========================================================
# 10. Résultats globaux
# =========================================================

all_results = []


# =========================================================
# 11. Boucle queries
# =========================================================

for _, query_row in queries.iterrows():

    query_id = str(
        query_row[
            "image_id"
        ]
    )


    query_sequence = str(
        query_row[
            "sequence"
        ]
    )


    print(
        "\n\n======================================"
    )

    print(
        "QUERY :",
        query_id
    )

    print(
        "======================================"
    )


    print(
        "Query sequence :",
        query_sequence
    )


    # =====================================================
    # 12. Charger query
    # =====================================================

    query_path = os.path.join(
        QUERY_IMAGE_DIR,
        f"{query_id}.jpg"
    )


    if not os.path.exists(
        query_path
    ):

        print(
            "[ERROR] Query image absente :",
            query_path
        )

        continue


    query_image = load_gray_image(
        query_path
    )


    if query_image is None:

        print(
            "[ERROR] Impossible de lire query."
        )

        continue


    query_keypoints, query_descriptors = (
        compute_sift(
            query_image
        )
    )


    if (
        query_keypoints is None
        or
        query_descriptors is None
    ):

        print(
            "[ERROR] Aucun descripteur SIFT query."
        )

        continue


    print(
        "Query keypoints :",
        len(query_keypoints)
    )


    # =====================================================
    # 13. Candidats GIS de la query
    # =====================================================

    query_gis = (
        gis[
            gis[
                "query"
            ]
            ==
            query_id
        ]
        .copy()
        .sort_values(
            "gis_score",
            ascending=False
        )
    )


    if query_gis.empty:

        print(
            "Aucun candidat GIS."
        )

        continue


    query_building_results = []


    # =====================================================
    # 14. Tester chaque bâtiment
    # =====================================================

    for _, gis_row in query_gis.iterrows():

        building_id = str(
            gis_row[
                "building_id"
            ]
        )


        gis_score = float(
            gis_row[
                "gis_score"
            ]
        )


        building_refs = (
            references[
                references[
                    "building_id"
                ]
                ==
                building_id
            ]
        )


        # =================================================
        # Aucun pool propre pour ce bâtiment
        # =================================================

        if building_refs.empty:

            print(
                building_id,
                "-> aucune référence propre"
            )


            query_building_results.append({

                "query":
                    query_id,

                "query_sequence":
                    query_sequence,

                "building_id":
                    building_id,

                "gis_score":
                    gis_score,

                "best_reference":
                    "",

                "reference_sequence":
                    "",

                "good_matches":
                    0,

                "inliers":
                    0,

                "inlier_ratio":
                    0.0,

                "filtered_same_sequence":
                    0
            })


            continue


        # =================================================
        # Meilleure référence du bâtiment
        # =================================================

        best_result = None

        filtered_same_sequence = 0


        for _, ref_row in building_refs.iterrows():

            reference_id = str(
                ref_row[
                    "reference_image_id"
                ]
            )


            reference_sequence = str(
                ref_row[
                    "sequence"
                ]
            )


            # =============================================
            # ANTI-LEAKAGE
            # =============================================

            if (
                query_sequence
                and
                reference_sequence
                and
                query_sequence
                ==
                reference_sequence
            ):

                filtered_same_sequence += 1

                continue


            key = (
                building_id,
                reference_id
            )


            ref_features = (
                reference_features.get(
                    key
                )
            )


            if ref_features is None:
                continue


            result = match_images(

                query_keypoints,
                query_descriptors,

                ref_features[
                    "keypoints"
                ],

                ref_features[
                    "descriptors"
                ]
            )


            candidate = {

                "reference_id":
                    reference_id,

                "reference_sequence":
                    reference_sequence,

                "good_matches":
                    result[
                        "good_matches"
                    ],

                "inliers":
                    result[
                        "inliers"
                    ],

                "inlier_ratio":
                    result[
                        "inlier_ratio"
                    ]
            }


            # =============================================
            # Meilleure référence :
            # 1. inliers
            # 2. inlier ratio
            # 3. good matches
            # =============================================

            if best_result is None:

                best_result = candidate

            else:

                current_key = (

                    candidate[
                        "inliers"
                    ],

                    candidate[
                        "inlier_ratio"
                    ],

                    candidate[
                        "good_matches"
                    ]
                )


                best_key = (

                    best_result[
                        "inliers"
                    ],

                    best_result[
                        "inlier_ratio"
                    ],

                    best_result[
                        "good_matches"
                    ]
                )


                if (
                    current_key
                    >
                    best_key
                ):

                    best_result = candidate


        # =================================================
        # Toutes références filtrées
        # =================================================

        if best_result is None:

            print(

                building_id,

                "-> aucune référence utilisable",

                "| filtered_same_sequence:",

                filtered_same_sequence
            )


            query_building_results.append({

                "query":
                    query_id,

                "query_sequence":
                    query_sequence,

                "building_id":
                    building_id,

                "gis_score":
                    gis_score,

                "best_reference":
                    "",

                "reference_sequence":
                    "",

                "good_matches":
                    0,

                "inliers":
                    0,

                "inlier_ratio":
                    0.0,

                "filtered_same_sequence":
                    filtered_same_sequence
            })


            continue


        # =================================================
        # Affichage
        # =================================================

        print(

            building_id,

            "| GIS:",
            round(
                gis_score,
                4
            ),

            "| ref:",
            best_result[
                "reference_id"
            ],

            "| matches:",
            best_result[
                "good_matches"
            ],

            "| inliers:",
            best_result[
                "inliers"
            ],

            "| ratio:",
            round(
                best_result[
                    "inlier_ratio"
                ],
                3
            ),

            "| filtered_same_seq:",
            filtered_same_sequence
        )


        query_building_results.append({

            "query":
                query_id,

            "query_sequence":
                query_sequence,

            "building_id":
                building_id,

            "gis_score":
                gis_score,

            "best_reference":
                best_result[
                    "reference_id"
                ],

            "reference_sequence":
                best_result[
                    "reference_sequence"
                ],

            "good_matches":
                best_result[
                    "good_matches"
                ],

            "inliers":
                best_result[
                    "inliers"
                ],

            "inlier_ratio":
                best_result[
                    "inlier_ratio"
                ],

            "filtered_same_sequence":
                filtered_same_sequence
        })


    # =====================================================
    # 15. Normalisation vision
    # =====================================================

    if not query_building_results:
        continue


    max_inliers = max(

        result[
            "inliers"
        ]

        for result
        in query_building_results
    )


    # =====================================================
    # 16. Vision score + fusion
    # =====================================================

    for result in query_building_results:

        if max_inliers > 0:

            normalized_inliers = (

                result[
                    "inliers"
                ]
                /
                max_inliers
            )

        else:

            normalized_inliers = 0.0


        vision_score = (

            0.5
            *
            normalized_inliers

            +

            0.5
            *
            result[
                "inlier_ratio"
            ]
        )


        final_score = (

            VISION_WEIGHT
            *
            vision_score

            +

            GIS_WEIGHT
            *
            result[
                "gis_score"
            ]
        )


        result[
            "normalized_inliers"
        ] = normalized_inliers


        result[
            "vision_score"
        ] = vision_score


        result[
            "final_score"
        ] = final_score


    # =====================================================
    # 17. Ranking final
    # =====================================================

    query_building_results = sorted(

        query_building_results,

        key=lambda x:
            x[
                "final_score"
            ],

        reverse=True
    )


    for rank, result in enumerate(
        query_building_results,
        start=1
    ):

        result[
            "rank"
        ] = rank


    # =====================================================
    # 18. Affichage ranking
    # =====================================================

    print(
        "\nRANKING FINAL"
    )


    for result in query_building_results:

        print(

            f"#{result['rank']}",

            result[
                "building_id"
            ],

            "| GIS:",
            round(
                result[
                    "gis_score"
                ],
                4
            ),

            "| vision:",
            round(
                result[
                    "vision_score"
                ],
                4
            ),

            "| final:",
            round(
                result[
                    "final_score"
                ],
                4
            ),

            "| inliers:",
            result[
                "inliers"
            ],

            "| ref:",
            result[
                "best_reference"
            ]
        )


    prediction = (
        query_building_results[0]
    )


    print(
        "\nPREDICTION :",
        prediction[
            "building_id"
        ]
    )


    print(
        "Final score :",
        round(
            prediction[
                "final_score"
            ],
            6
        )
    )


    all_results.extend(
        query_building_results
    )


# =========================================================
# 19. Sauvegarde finale
# =========================================================

results_df = pd.DataFrame(
    all_results
)


if not results_df.empty:

    columns = [

        "query",

        "query_sequence",

        "building_id",

        "rank",

        "gis_score",

        "best_reference",

        "reference_sequence",

        "good_matches",

        "inliers",

        "inlier_ratio",

        "normalized_inliers",

        "vision_score",

        "final_score",

        "filtered_same_sequence"
    ]


    results_df = results_df[
        columns
    ]


results_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 20. Résumé
# =========================================================

print(
    "\n\n======================================"
)

print(
    "BATCH FUSION SUBSET V1 CLEAN TERMINÉ"
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

    evaluated_queries = (
        results_df[
            "query"
        ]
        .nunique()
    )


    print(
        "Queries avec résultat :",
        evaluated_queries
    )


    print(
        "\n======================================"
    )

    print(
        "TOP-1 PREDICTIONS"
    )

    print(
        "======================================"
    )


    top1 = (
        results_df[
            results_df[
                "rank"
            ]
            ==
            1
        ]
        .copy()
    )


    print(

        top1[
            [
                "query",
                "building_id",
                "gis_score",
                "vision_score",
                "final_score",
                "best_reference",
                "inliers",
                "inlier_ratio",
                "filtered_same_sequence"
            ]
        ]
        .to_string(
            index=False
        )
    )


    # =====================================================
    # 21. Statistiques anti-leakage
    # =====================================================

    total_filtered = int(

        results_df[
            "filtered_same_sequence"
        ]
        .sum()
    )


    print(
        "\nRéférences same-sequence filtrées :",
        total_filtered
    )


    # =====================================================
    # 22. Vérification leakage
    # =====================================================

    used_reference_mask = (

        results_df[
            "best_reference"
        ]
        .fillna("")
        .astype(str)
        !=
        ""
    )


    same_sequence_mask = (

        results_df[
            "query_sequence"
        ]
        .fillna("")
        .astype(str)
        ==
        results_df[
            "reference_sequence"
        ]
        .fillna("")
        .astype(str)
    )


    leakage_rows = (

        results_df[
            used_reference_mask
            &
            same_sequence_mask
        ]
    )


    print(
        "Fuites de séquence restantes :",
        len(leakage_rows)
    )


    if not leakage_rows.empty:

        print(
            "\n[WARNING] Leakage détecté !"
        )


        print(

            leakage_rows[
                [
                    "query",
                    "building_id",
                    "best_reference",
                    "query_sequence",
                    "reference_sequence"
                ]
            ]
            .to_string(
                index=False
            )
        )


    else:

        print(
            "ANTI-LEAKAGE : OK"
        )


    # =====================================================
    # 23. Statistique bâtiments sans vision
    # =====================================================

    no_reference_rows = (

        results_df[
            results_df[
                "best_reference"
            ]
            .fillna("")
            .astype(str)
            ==
            ""
        ]
    )


    print(
        "Lignes sans référence vision :",
        len(no_reference_rows)
    )


print(
    "\nTerminé."
)
