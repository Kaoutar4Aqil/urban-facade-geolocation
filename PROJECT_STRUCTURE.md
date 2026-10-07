# Project Structure

```text
urban-facade-geolocation/
│
├── data/
│   ├── raw/
│   │   ├── images/
│   │   ├── osm/
│   │   ├── query_subset_v1/
│   │   ├── reference_images/
│   │   ├── reference_pool/
│   │   ├── reference_pool_v2/
│   │   └── reference_pool_subset_v3/
│   │
│   ├── metadata/
│   │   ├── query_pool_v1.csv
│   │   ├── query_subset_v1.csv
│   │   ├── ground_truth.csv
│   │   └── ground_truth_subset_v1.csv
│   │
│   └── processed/
│       ├── paris_buildings_clean.geojson
│       ├── batch_gis_candidates_subset_v1.csv
│       ├── reference_pool_subset_v3.csv
│       ├── reference_pool_subset_v3_clean.csv
│       ├── batch_final_predictions_subset_v1_clean.csv
│       ├── ground_truth_maps_subset_v1/
│       └── evaluation_plots/
│
├── download_buildings.py
├── clean_buildings.py
├── build_query_pool_v1.py
├── select_query_subset_v1.py
├── download_query_subset_v1.py
├── batch_gis_candidates_subset_v1.py
├── build_reference_pool_subset_v3.py
├── download_reference_pool_subset_v3.py
├── check_reference_ambiguity.py
├── clean_reference_pool_v3.py
├── batch_fusion_subset_v1.py
├── build_ground_truth_subset_v1.py
├── generate_ground_truth_maps_subset_v1.py
├── evaluate_subset_v1_final.py
├── generate_evaluation_plots.py
├── run_final_evaluation.py
│
├── README.md
├── PROJECT_STRUCTURE.md
├── requirements.txt
├── .gitignore
└── .env                 # Local only - never committed
