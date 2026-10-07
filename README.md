# Urban Facade Geolocation and Building Matching Using GIS and Computer Vision

## Overview

This project implements a hybrid pipeline for **urban facade geolocation and building matching** by combining Geographic Information Systems (GIS) with classical computer vision.

The system uses:

- Mapillary street-level imagery
- OpenStreetMap building footprints
- geographic coordinates
- camera heading
- GIS-based candidate generation
- SIFT local feature extraction
- Lowe's ratio test
- RANSAC geometric verification
- GIS and computer-vision score fusion
- manual ground-truth verification
- quantitative evaluation

The objective is to identify the building observed in a street-level query image among nearby urban building footprints.

The project was developed as a reproducible research-oriented workflow under **WSL / Ubuntu and Python**.

---

## 1. Problem Statement

Given a street-level query image associated with:

- GPS coordinates
- camera heading
- image metadata

the objective is to determine which nearby building corresponds to the visible facade.

Urban facade matching is challenging because of:

- repetitive architectural patterns
- visually similar neighboring buildings
- GPS uncertainty
- noisy or inaccurate compass headings
- viewpoint variations
- illumination changes
- occlusions
- vegetation
- cars and pedestrians
- different image acquisition dates
- multiple buildings visible in the same scene

To improve robustness, this project combines two complementary sources of information:

1. **GIS-based geometric reasoning**
2. **Computer-vision-based facade matching**

---

## 2. Pipeline

The complete workflow is:

```text
Mapillary Query Image
        |
        v
GPS + Camera Heading
        |
        v
OpenStreetMap Buildings
        |
        v
GIS Candidate Generation
        |
        v
Candidate Buildings
        |
        v
Reference Image Pool
        |
        v
SIFT Feature Extraction
        |
        v
Lowe Ratio Test
        |
        v
RANSAC Geometric Verification
        |
        v
Vision Score
        |
        +----------------+
        |                |
        v                v
   GIS Score        Vision Score
        |                |
        +-------+--------+
                |
                v
           Score Fusion
                |
                v
          Final Ranking
                |
                v
       Predicted Building
```

The final predictions are compared against a manually verified ground-truth dataset.

---

## 3. GIS Candidate Generation

The GIS component uses:

- query latitude and longitude
- camera heading
- OpenStreetMap building footprints
- geometric visibility constraints
- distance and orientation information

Nearby buildings are filtered and ranked according to their geometric compatibility with the query camera.

The GIS stage reduces the search space before visual matching.

For the final evaluated subset:

- **30 query images**
- **26 queries with GIS candidates**
- **4 queries without GIS candidates**
- **72 query-building candidate pairs**

---

## 4. Reference Image Pool

For each candidate building, Mapillary images are collected to create a reference pool.

The raw reference pool contained:

- **217 building-reference associations**
- **30 buildings**
- **170 unique reference images**

Some Mapillary images were associated with multiple building labels and were therefore considered ambiguous.

After ambiguity filtering:

- **144 clean reference images**
- **26 buildings**
- **0 remaining ambiguous reference images**

Four building labels lost all reference images after ambiguity removal.

This cleaning step prevents the same reference image from being assigned to multiple buildings during visual matching.

---

## 5. Visual Matching

The visual component is based on classical local-feature matching.

### SIFT

SIFT is used to detect and describe local keypoints in both query and reference images.

### Lowe's Ratio Test

Descriptor matches are filtered using Lowe's ratio test to remove ambiguous nearest-neighbor correspondences.

### RANSAC

RANSAC is used to estimate geometric consistency between matched keypoints.

The number of geometrically consistent inliers contributes to the visual matching score.

The visual pipeline therefore considers both:

- appearance similarity
- geometric consistency

---

## 6. Sequence Leakage Prevention

Street-level imagery frequently contains several consecutive images from the same Mapillary sequence.

Using a reference image originating from the same sequence as the query can artificially inflate performance.

To avoid this issue, references belonging to the same Mapillary sequence as the query are filtered before matching.

Final verification showed:

- **18 same-sequence references filtered**
- **0 remaining sequence leaks**

This anti-leakage procedure is important for obtaining a more realistic evaluation.

---

## 7. Score Fusion

Each building candidate receives two scores:

- GIS score
- vision score

The current experimental fusion uses:

```text
Final Score = 0.4 × GIS Score + 0.6 × Vision Score
```

The weights were kept fixed during the final experiment.

The purpose of fusion is to combine geographic plausibility with visual evidence.

However, the final evaluation shows that visual fusion does not always improve Top-1 ranking.

---

## 8. Ground Truth

A manual ground-truth annotation workflow was implemented.

Each query was independently reviewed using:

- the original street-level image
- a GIS visualization
- candidate building polygons
- camera position
- camera heading

Possible labels include:

```text
Bxxxx
```

for a verified building, or:

```text
NO_BUILDING
```

when no target building can be reliably assigned.

Final ground truth:

- **30 queries**
- **30 verified annotations**
- **0 pending annotations**

---

## 9. Final Evaluation

The final pipeline was evaluated on the manually verified 30-query subset.

### Results

| Metric | Result |
|---|---:|
| GIS Top-1 Accuracy | **83.33%** |
| Fusion Top-1 Accuracy | **76.67%** |
| Fusion Top-3 Accuracy | **86.67%** |
| GIS Candidate Recall | **88.46%** |
| NO_BUILDING Accuracy | **100.00%** |
| GIS Top-1 Errors | **5** |
| Fusion Top-1 Errors | **7** |
| Cases corrected by fusion | **0** |
| Cases degraded by fusion | **2** |

---

## 10. Interpretation

The GIS-only method achieved the strongest Top-1 result:

```text
GIS Top-1 = 83.33%
```

The current fusion strategy achieved:

```text
Fusion Top-1 = 76.67%
```

Therefore, the current visual fusion does **not improve Top-1 accuracy** on this experimental subset.

Two queries that were correctly ranked by GIS were degraded after adding the visual score.

However, the fusion achieves:

```text
Fusion Top-3 = 86.67%
```

This suggests that the computer-vision component can still place the correct building among the highest-ranked candidates, even when it does not select it as Top-1.

The result indicates that future work should focus on better score calibration and more robust visual confidence estimation rather than simply increasing the influence of the vision score.

---

## 11. Error Analysis

The final evaluation identified:

```text
GIS errors:        5
Fusion errors:     7
Fusion improvements: 0
Fusion degradations: 2
```

The two cases degraded by fusion were:

```text
275453527531880
138973908264709
```

These cases show that a high visual similarity score can sometimes override a correct GIS prediction.

This can occur because urban facades frequently contain repeated visual structures such as:

- windows
- balconies
- stone textures
- storefront patterns
- architectural ornaments

A high number of SIFT/RANSAC correspondences does not necessarily guarantee that two images correspond to the same physical building.

---

## 12. Evaluation Outputs

The evaluation pipeline generates:

```text
data/processed/evaluation_subset_v1_details.csv
data/processed/evaluation_subset_v1_summary.csv
```

The visualization script generates:

```text
data/processed/evaluation_plots/
```

including:

```text
accuracy_comparison.png
gis_candidate_recall.png
gis_correct_vs_wrong.png
fusion_correct_vs_wrong.png
fusion_score_distribution.png
fusion_inliers_boxplot.png
gis_score_boxplot.png
vision_score_boxplot.png
gis_vs_fusion_score.png
fusion_errors.csv
fusion_improvements.csv
fusion_degradations.csv
```

---

## 13. Main Final Scripts

The final experimental workflow relies mainly on:

```text
clean_buildings.py
build_query_pool_v1.py
select_query_subset_v1.py
download_query_subset_v1.py

batch_gis_candidates_subset_v1.py

build_reference_pool_subset_v3.py
download_reference_pool_subset_v3.py
check_reference_ambiguity.py
clean_reference_pool_v3.py
check_sequence_leakage.py

batch_fusion_subset_v1.py

build_ground_truth_subset_v1.py
generate_ground_truth_maps_subset_v1.py
annotate_ground_truth.py

evaluate_subset_v1_final.py
generate_evaluation_plots.py
run_final_evaluation.py
```

Experimental and previous development versions are stored in:

```text
archive/
```

---

## 14. Project Structure

```text
urban-facade-geolocation/
│
├── archive/
│   ├── debug_tools/
│   └── previous experimental scripts
│
├── data/
│   ├── metadata/
│   ├── processed/
│   └── raw/
│
├── annotate_ground_truth.py
├── batch_fusion_subset_v1.py
├── batch_gis_candidates_subset_v1.py
├── build_ground_truth_subset_v1.py
├── build_query_pool_v1.py
├── build_reference_pool_subset_v3.py
├── check_reference_ambiguity.py
├── check_sequence_leakage.py
├── clean_buildings.py
├── clean_reference_pool_v3.py
├── download_query_subset_v1.py
├── download_reference_pool_subset_v3.py
├── evaluate_subset_v1_final.py
├── generate_evaluation_plots.py
├── generate_ground_truth_maps_subset_v1.py
├── restore_original_30_queries.py
├── run_final_evaluation.py
├── select_query_subset_v1.py
│
├── PROJECT_STRUCTURE.md
├── requirements.txt
├── README.md
└── .gitignore
```

Large raw image datasets and generated temporary files are excluded from Git where appropriate.

---

## 15. Installation

Clone the repository:

```bash
git clone <repository-url>
cd urban-facade-geolocation
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## 16. Environment Variables

Mapillary API credentials must not be committed to GitHub.

Create a local `.env` file:

```text
MAPILLARY_ACCESS_TOKEN=your_token_here
```

The `.env` file is excluded through `.gitignore`.

---

## 17. Running the Final Evaluation

After the required metadata, GIS candidates, predictions and ground truth are available, run:

```bash
python run_final_evaluation.py
```

A successful execution finishes with:

```text
PIPELINE D'ÉVALUATION TERMINÉ
STATUS : OK
```

---

## 18. Technologies

### Programming

- Python

### GIS

- GeoPandas
- Shapely
- OSMnx
- OpenStreetMap
- Folium

### Computer Vision

- OpenCV
- SIFT
- Lowe's Ratio Test
- RANSAC

### Data Processing

- Pandas
- NumPy

### Visualization

- Matplotlib
- Folium

### Environment

- Ubuntu
- WSL
- Python virtual environments
- Git
- GitHub

---

## 19. Limitations

The current evaluation is based on a relatively small manually verified subset of 30 queries.

The current visual pipeline also relies on handcrafted SIFT descriptors, which may be sensitive to:

- large viewpoint changes
- strong illumination differences
- repetitive facade structures
- low-texture surfaces
- significant temporal changes

The current GIS/vision fusion weights are heuristic and were not learned from a separate validation dataset.

Therefore, the reported metrics should be interpreted as experimental results for this specific subset rather than as general performance estimates for all urban environments.

---

## 20. Future Work

Possible improvements include:

- larger independently annotated datasets
- automatic fusion-weight calibration
- confidence-aware fusion
- learned local features
- SuperPoint / SuperGlue
- LightGlue
- global image retrieval embeddings
- CLIP or DINO-based facade representations
- semantic facade segmentation
- uncertainty-aware GPS modeling
- improved camera-heading modeling
- multi-view reference aggregation
- sequence-level reasoning
- spatial graph reasoning
- learned candidate re-ranking

A particularly important future direction is to use the vision module as a confidence-aware re-ranker rather than allowing uncertain visual matches to override strong GIS evidence.

---

## Conclusion

This project demonstrates a complete experimental pipeline for urban facade geolocation and building matching using GIS and computer vision.

The final experiment shows that GIS information provides a strong baseline, achieving **83.33% Top-1 accuracy**.

The current GIS/vision fusion reaches **86.67% Top-3 accuracy**, but decreases Top-1 accuracy to **76.67%**, highlighting the importance of robust visual confidence calibration.

The project therefore provides both a functional geolocation pipeline and an experimental framework for studying how geographic and visual information can be combined for urban building recognition.
