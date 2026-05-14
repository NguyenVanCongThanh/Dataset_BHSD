# Study Ingestion Pipeline Guide

This document explains how to use the automated pipeline to add and visualize external CT studies (300+ files).

## Pipeline Overview

The pipeline consists of two main phases:

1. **Phase 1: Ingestion & Visualization**: Processes `.nii.gz` files, reorients them to LAS, generates PNG slices/montages, and maps labels.
2. **Phase 2: UI Synchronization**: Consolidates the new data into the web viewer's JSON database.

## Prerequisites

- Python 3.10+
- Dependencies: `nibabel`, `pandas`, `numpy`, `pillow`, `matplotlib`, `tqdm`
- **Source Data**: Place all `.nii.gz` files in `/mnt/d/all_EDH_studies_Exclude_BHSD`.
- **Naming Convention**: Files must follow the format `PatientID_StudyID.nii.gz`.

## Execution

You can run the entire pipeline with a single command:

```bash
# Process ALL new studies
python3 run_pipeline.py

# Process a limited batch (e.g., 50 studies) to test
python3 run_pipeline.py --limit 50
```

## Script Details

### 1. `scripts/add_external_studies.py`

This is the core engine. It handles:

- **Incremental Processing**: Skips studies already listed in `added_external_studies.csv`.
- **LAS Reorientation**: Enforces Left-Anterior-Superior orientation on the NIfTI files.
- **180-Degree Rotation**: Generates slices and montages with a 180-degree rotation (Anterior at Bottom) as per the latest requirements.
- **Robust Label Mapping**: Synchronizes slice labels directly from `metadata.csv` and `stage_2_train.csv` ensuring 100% accuracy.
- **HU Windowing**: Applies Brain Window (W:80, L:40) for medical-grade visualization.

### 2. `scripts/create_global_viewer.py`

This script updates `study_visualizations/data/studies_list.json`. It scans the `study_visualizations` directory and ensures the web UI knows about every processed study.

## Monitoring & Tracking

- **Tracking File**: `added_external_studies.csv` lists all successfully integrated external studies.
- **Individual Study Data**: Each study has its own folder in `study_visualizations/` containing:
  - `slices/*.png`: Individual slice images.
  - `[StudyID]_montage.png`: A comprehensive overview image.
  - `[StudyID].csv`: Metadata and labels for each slice.

## Troubleshooting

- **Orientation issues**: If images appear flipped, the logic is centrally controlled in `scripts/add_external_studies.py` (look for `fixed_orientation = np.fliplr(windowed.T)`).
- **Missing Metadata**: If a study is skipped with "No metadata found", verify the `StudyInstanceUID` in `csv_files/raw/metadata.csv`.
- **BHSD Studies**: The pipeline is designed to **skip** BHSD studies. Do not use this pipeline to modify BHSD data.

## Verification

After running the pipeline, open `study_visualizations/index.html` in your browser to verify the new studies are listed and correctly visualized.
