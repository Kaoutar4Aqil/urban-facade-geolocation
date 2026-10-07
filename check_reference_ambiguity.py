import pandas as pd


PATH = (
    "data/processed/"
    "reference_pool_subset_v3.csv"
)

OUTPUT = (
    "data/processed/"
    "reference_ambiguity_v3.csv"
)


df = pd.read_csv(
    PATH
)

df["reference_image_id"] = (
    df["reference_image_id"]
    .astype(str)
)

df["building_id"] = (
    df["building_id"]
    .astype(str)
)


# Nombre de bâtiments associés
# à chaque image de référence
counts = (
    df.groupby(
        "reference_image_id"
    )["building_id"]
    .nunique()
)


ambiguous_ids = (
    counts[
        counts > 1
    ]
    .index
)


ambiguous = (
    df[
        df[
            "reference_image_id"
        ]
        .isin(
            ambiguous_ids
        )
    ]
    .sort_values(
        [
            "reference_image_id",
            "building_id"
        ]
    )
)


print(
    "Nombre total de références :",
    df[
        "reference_image_id"
    ].nunique()
)


print(
    "Images associées à plusieurs bâtiments :",
    len(
        ambiguous_ids
    )
)


if not ambiguous.empty:

    print(
        "\n======================================"
    )

    print(
        "RÉFÉRENCES AMBIGUËS"
    )

    print(
        "======================================"
    )


    for reference_id, group in (
        ambiguous.groupby(
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


ambiguous.to_csv(
    OUTPUT,
    index=False
)


print(
    "\nFichier sauvegardé :",
    OUTPUT
)
