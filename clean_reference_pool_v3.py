import pandas as pd


# =========================================================
# 1. Chemins
# =========================================================

INPUT_PATH = (
    "data/processed/"
    "reference_pool_subset_v3.csv"
)

OUTPUT_PATH = (
    "data/processed/"
    "reference_pool_subset_v3_clean.csv"
)

REMOVED_PATH = (
    "data/processed/"
    "reference_pool_subset_v3_removed_ambiguous.csv"
)


# =========================================================
# 2. Charger les références
# =========================================================

df = pd.read_csv(
    INPUT_PATH
)


df["reference_image_id"] = (
    df["reference_image_id"]
    .astype(str)
)

df["building_id"] = (
    df["building_id"]
    .astype(str)
)


print(
    "Nombre de lignes initiales :",
    len(df)
)

print(
    "Nombre d'images uniques initiales :",
    df["reference_image_id"].nunique()
)

print(
    "Nombre de bâtiments initialement couverts :",
    df["building_id"].nunique()
)


# =========================================================
# 3. Détecter les images ambiguës
# =========================================================

building_counts = (
    df
    .groupby(
        "reference_image_id"
    )["building_id"]
    .nunique()
)


ambiguous_ids = set(
    building_counts[
        building_counts > 1
    ].index
)


print(
    "\nImages ambiguës détectées :",
    len(ambiguous_ids)
)


# =========================================================
# 4. Afficher les références ambiguës
# =========================================================

if ambiguous_ids:

    print(
        "\n======================================"
    )

    print(
        "RÉFÉRENCES AMBIGUËS À SUPPRIMER"
    )

    print(
        "======================================"
    )


    ambiguous_df = (
        df[
            df[
                "reference_image_id"
            ]
            .isin(
                ambiguous_ids
            )
        ]
        .copy()
        .sort_values(
            [
                "reference_image_id",
                "building_id"
            ]
        )
    )


    for reference_id, group in (
        ambiguous_df.groupby(
            "reference_image_id"
        )
    ):

        buildings = (
            group[
                "building_id"
            ]
            .tolist()
        )


        print(
            reference_id,
            "->",
            buildings
        )

else:

    ambiguous_df = pd.DataFrame(
        columns=df.columns
    )


# =========================================================
# 5. Retirer toutes les images ambiguës
# =========================================================

clean_df = (
    df[
        ~df[
            "reference_image_id"
        ]
        .isin(
            ambiguous_ids
        )
    ]
    .copy()
)


# =========================================================
# 6. Supprimer éventuels doublons exacts
# =========================================================

clean_df = (
    clean_df
    .drop_duplicates(
        subset=[
            "reference_image_id"
        ],
        keep="first"
    )
    .reset_index(
        drop=True
    )
)


# =========================================================
# 7. Sauvegarder les références supprimées
# =========================================================

ambiguous_df.to_csv(
    REMOVED_PATH,
    index=False
)


# =========================================================
# 8. Sauvegarder le pool propre
# =========================================================

clean_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 9. Vérifier les ambiguïtés restantes
# =========================================================

remaining_counts = (
    clean_df
    .groupby(
        "reference_image_id"
    )["building_id"]
    .nunique()
)


remaining_ambiguous = (
    remaining_counts[
        remaining_counts > 1
    ]
)


# =========================================================
# 10. Statistiques de couverture
# =========================================================

covered_buildings = (
    clean_df[
        "building_id"
    ]
    .nunique()
)


refs_per_building = (
    clean_df
    .groupby(
        "building_id"
    )
    .size()
    .sort_index()
)


# =========================================================
# 11. Bâtiments perdus après nettoyage
# =========================================================

initial_buildings = set(
    df[
        "building_id"
    ]
    .unique()
)


clean_buildings = set(
    clean_df[
        "building_id"
    ]
    .unique()
)


lost_buildings = sorted(
    initial_buildings
    -
    clean_buildings
)


# =========================================================
# 12. Résumé final
# =========================================================

print(
    "\n======================================"
)

print(
    "NETTOYAGE TERMINÉ"
)

print(
    "======================================"
)


print(
    "Lignes initiales :",
    len(df)
)


print(
    "Lignes restantes :",
    len(clean_df)
)


print(
    "Images uniques initiales :",
    df[
        "reference_image_id"
    ]
    .nunique()
)


print(
    "Images uniques restantes :",
    clean_df[
        "reference_image_id"
    ]
    .nunique()
)


print(
    "Images ambiguës supprimées :",
    len(ambiguous_ids)
)


print(
    "Bâtiments couverts :",
    covered_buildings
)


print(
    "Ambiguïtés restantes :",
    len(
        remaining_ambiguous
    )
)


print(
    "\n======================================"
)

print(
    "RÉFÉRENCES PAR BÂTIMENT"
)

print(
    "======================================"
)


if not refs_per_building.empty:

    print(
        refs_per_building
    )

else:

    print(
        "Aucune référence restante."
    )


print(
    "\n======================================"
)

print(
    "BÂTIMENTS COMPLÈTEMENT PERDUS"
)

print(
    "======================================"
)


print(
    "Nombre :",
    len(lost_buildings)
)


if lost_buildings:

    for building_id in lost_buildings:

        print(
            "-",
            building_id
        )

else:

    print(
        "Aucun bâtiment perdu."
    )


# =========================================================
# 13. Fichiers générés
# =========================================================

print(
    "\n======================================"
)

print(
    "FICHIERS"
)

print(
    "======================================"
)


print(
    "Pool nettoyé :",
    OUTPUT_PATH
)


print(
    "Références ambiguës supprimées :",
    REMOVED_PATH
)


# =========================================================
# 14. Contrôle final
# =========================================================

print(
    "\n======================================"
)

print(
    "VÉRIFICATION FINALE"
)

print(
    "======================================"
)


if len(
    remaining_ambiguous
) == 0:

    print(
        "STATUS : OK"
    )

    print(
        "Chaque image de référence restante "
        "est associée à un seul bâtiment."
    )

else:

    print(
        "STATUS : ERREUR"
    )

    print(
        "Il reste des images associées "
        "à plusieurs bâtiments."
    )
