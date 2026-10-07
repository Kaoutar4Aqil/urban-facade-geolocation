import os
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

GROUND_TRUTH_PATH = "data/metadata/ground_truth_subset_v1.csv"
QUERY_IMAGE_DIR = "data/raw/query_subset_v1"
MAP_DIR = "data/processed/ground_truth_maps_subset_v1"


# ============================================================
# CHARGEMENT
# ============================================================

if not os.path.exists(GROUND_TRUTH_PATH):
    raise FileNotFoundError(
        f"Fichier introuvable : {GROUND_TRUTH_PATH}"
    )

df = pd.read_csv(
    GROUND_TRUTH_PATH,
    dtype={"query_id": str}
)


# ============================================================
# FORCER LES COLONNES TEXTE
# ============================================================

text_columns = [
    "true_building_id",
    "status",
    "verification_method",
    "notes",
]

for col in text_columns:

    if col not in df.columns:
        df[col] = ""

    df[col] = (
        df[col]
        .fillna("")
        .astype(str)
    )


# ============================================================
# RÉSUMÉ INITIAL
# ============================================================

verified_count = (
    df["status"]
    .str.lower()
    .eq("verified")
    .sum()
)

pending_count = len(df) - verified_count


print()
print("======================================")
print("ANNOTATION MANUELLE GROUND TRUTH")
print("======================================")
print("Total :", len(df))
print("Verified :", verified_count)
print("Restantes :", pending_count)


# ============================================================
# BOUCLE D'ANNOTATION
# ============================================================

for index, row in df.iterrows():

    query_id = str(
        row["query_id"]
    )

    status = str(
        row["status"]
    ).strip().lower()

    true_building_id = str(
        row["true_building_id"]
    ).strip()


    # --------------------------------------------------------
    # DÉJÀ VÉRIFIÉ
    # --------------------------------------------------------

    if (
        status == "verified"
        and true_building_id != ""
    ):

        print()
        print(
            f"[SKIP] {query_id} -> {true_building_id}"
        )

        continue


    # --------------------------------------------------------
    # INFORMATIONS QUERY
    # --------------------------------------------------------

    print()
    print("======================================")
    print(f"QUERY {index + 1}/{len(df)}")
    print("======================================")

    print("Query ID :", query_id)

    if "gis_candidate_count" in df.columns:
        print(
            "Nombre candidats GIS :",
            row.get(
                "gis_candidate_count",
                ""
            )
        )

    if "gis_top1_for_reference_only" in df.columns:
        print(
            "GIS Top-1 informatif :",
            row.get(
                "gis_top1_for_reference_only",
                ""
            )
        )

    if "fusion_top1_for_reference_only" in df.columns:
        print(
            "Fusion Top-1 informatif :",
            row.get(
                "fusion_top1_for_reference_only",
                ""
            )
        )


    # --------------------------------------------------------
    # CHEMINS IMAGE + CARTE
    # --------------------------------------------------------

    image_path = os.path.join(
        QUERY_IMAGE_DIR,
        f"{query_id}.jpg"
    )

    map_path = os.path.join(
        MAP_DIR,
        f"{query_id}.html"
    )

    print()
    print("Image :")
    print(image_path)

    print()
    print("Carte :")
    print(map_path)


    # --------------------------------------------------------
    # INSTRUCTIONS
    # --------------------------------------------------------

    print()
    print(
        "Vérifie manuellement l'image et la carte."
    )

    print()
    print("Valeurs possibles :")
    print("  Bxxxx       -> bâtiment vérifié")
    print("  NO_BUILDING -> aucun bâtiment cible")
    print("  SKIP        -> passer pour l'instant")
    print("  QUIT        -> sauvegarder et quitter")


    # --------------------------------------------------------
    # SAISIE
    # --------------------------------------------------------

    while True:

        value = input(
            "\ntrue_building_id : "
        ).strip().upper()


        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if value == "QUIT":

            df.to_csv(
                GROUND_TRUTH_PATH,
                index=False
            )

            print()
            print("======================================")
            print("SAUVEGARDE EFFECTUÉE")
            print("======================================")
            print(
                "Fichier :",
                GROUND_TRUTH_PATH
            )
            print(
                "Programme arrêté."
            )

            raise SystemExit(0)


        # ----------------------------------------------------
        # SKIP
        # ----------------------------------------------------

        if value == "SKIP":

            print(
                "[SKIP] Query laissée en pending."
            )

            break


        # ----------------------------------------------------
        # NO_BUILDING
        # ----------------------------------------------------

        if value == "NO_BUILDING":

            df.loc[
                index,
                "true_building_id"
            ] = "NO_BUILDING"

            df.loc[
                index,
                "status"
            ] = "verified"

            df.loc[
                index,
                "verification_method"
            ] = (
                "manual_image_map_verification"
            )

            df.loc[
                index,
                "notes"
            ] = (
                "No clear target building visible "
                "after manual image and map verification."
            )

            df.to_csv(
                GROUND_TRUTH_PATH,
                index=False
            )

            print()
            print(
                f"[OK] {query_id} -> NO_BUILDING"
            )

            break


        # ----------------------------------------------------
        # BUILDING ID
        # ----------------------------------------------------

        valid_building = (
            value.startswith("B")
            and len(value) == 5
            and value[1:].isdigit()
        )

        if valid_building:

            df.loc[
                index,
                "true_building_id"
            ] = value

            df.loc[
                index,
                "status"
            ] = "verified"

            df.loc[
                index,
                "verification_method"
            ] = (
                "manual_image_map_verification"
            )

            df.loc[
                index,
                "notes"
            ] = (
                f"Building {value} verified "
                "from query image, camera heading "
                "and GIS map."
            )

            df.to_csv(
                GROUND_TRUTH_PATH,
                index=False
            )

            print()
            print(
                f"[OK] {query_id} -> {value}"
            )

            break


        # ----------------------------------------------------
        # ERREUR
        # ----------------------------------------------------

        print()
        print("[ERREUR] Valeur invalide.")
        print(
            "Utilise Bxxxx, NO_BUILDING, SKIP ou QUIT."
        )


# ============================================================
# RÉSUMÉ FINAL
# ============================================================

df = pd.read_csv(
    GROUND_TRUTH_PATH,
    dtype={"query_id": str}
)

verified = (
    df["status"]
    .fillna("")
    .astype(str)
    .str.lower()
    .eq("verified")
    .sum()
)

pending = len(df) - verified


print()
print("======================================")
print("ANNOTATION TERMINÉE")
print("======================================")

print("Total :", len(df))
print("Verified :", verified)
print("Pending :", pending)

print(
    "Fichier :",
    GROUND_TRUTH_PATH
)


if pending == 0:

    print()
    print("GROUND TRUTH COMPLET.")

    print()
    print(
        "Commande suivante :"
    )

    print(
        "python run_final_evaluation.py"
    )

else:

    print()
    print(
        f"Il reste {pending} query(s) à vérifier."
    )
