import pandas as pd


# =========================================================
# 1. Chemins
# =========================================================

INPUT_PATH = (
    "data/metadata/"
    "query_pool_v1.csv"
)

OUTPUT_PATH = (
    "data/metadata/"
    "query_subset_v1.csv"
)


# =========================================================
# 2. Paramètres
# =========================================================

MAX_IMAGES_PER_SEQUENCE = 2

TARGET_MAX_IMAGES = 30


# =========================================================
# 3. Charger pool
# =========================================================

df = pd.read_csv(
    INPUT_PATH
)


df["image_id"] = (
    df["image_id"]
    .astype(str)
)


print(
    "Nombre initial d'images :",
    len(df)
)


print(
    "Nombre de séquences :",
    df["sequence"].nunique()
)


# =========================================================
# 4. Trier par séquence + date
# =========================================================

df = df.sort_values(
    [
        "sequence",
        "captured_at"
    ]
)


# =========================================================
# 5. Maximum N images par séquence
# =========================================================

selected = (
    df
    .groupby(
        "sequence",
        group_keys=False
    )
    .head(
        MAX_IMAGES_PER_SEQUENCE
    )
    .copy()
)


# =========================================================
# 6. Limite globale
# =========================================================

selected = (
    selected
    .head(
        TARGET_MAX_IMAGES
    )
    .reset_index(
        drop=True
    )
)


# =========================================================
# 7. Sauvegarde
# =========================================================

selected.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "\n======================================"
)

print(
    "QUERY SUBSET V1"
)

print(
    "======================================"
)


print(
    "Nombre sélectionné :",
    len(selected)
)


print(
    "Nombre de séquences représentées :",
    selected["sequence"].nunique()
)


print(
    "\nImages par séquence :"
)

print(
    selected[
        "sequence"
    ]
    .value_counts()
)


print(
    "\nFichier sauvegardé :"
)

print(
    OUTPUT_PATH
)
