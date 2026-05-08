import os
import pandas as pd
import numpy as np
from tqdm import tqdm

def parse_z(pos_str):
    try:
        # Format is usually like "[-125. -18. 111.900024]" or "[-125, -18, 111.9]"
        # We handle both spaces and commas
        cleaned = pos_str.replace('[', '').replace(']', '').replace(',', ' ').split()
        return float(cleaned[-1])
    except:
        return 0.0

def sort_slices_by_z():
    metadata_path = "csv_files/raw/metadata.csv"
    train_labels_path = "csv_files/raw/stage_2_train.csv"
    base_dir = "study_visualizations"
    
    print("Loading metadata for sorting...")
    meta_df = pd.read_csv(metadata_path, usecols=['FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID', 'ImagePositionPatient'])
    
    print("Parsing Z-coordinates...")
    meta_df['Z_pos'] = meta_df['ImagePositionPatient'].apply(parse_z)
    
    print("Loading training labels...")
    train_df = pd.read_csv(train_labels_path).drop_duplicates(subset='ID')
    train_df[['ImageID', 'Subtype']] = train_df['ID'].str.rsplit('_', n=1, expand=True)
    pivot_df = train_df.pivot(index='ImageID', columns='Subtype', values='Label')
    
    study_ids = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    print(f"Sorting {len(study_ids)} studies...")

    subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural', 'any']

    for study_id in tqdm(study_ids):
        # 1. Get metadata for this study
        study_meta = meta_df[meta_df['StudyInstanceUID'] == study_id].copy()
        if study_meta.empty:
            print(f"Warning: No metadata found for {study_id}")
            continue
            
        # 2. Sort by Z_pos (Physical order)
        # Usually CT scans are sorted from feet to head or head to feet.
        # We sort by Z ascending.
        study_meta = study_meta.sort_values('Z_pos')
        
        # 3. Add SliceNumber (1-indexed)
        study_meta['SliceNumber'] = range(1, len(study_meta) + 1)
        
        # 4. Join with labels
        study_meta['ImageID'] = study_meta['FileName'].str.replace('.dcm', '', regex=False)
        final_df = study_meta.merge(pivot_df, left_on='ImageID', right_index=True, how='left')
        
        # 5. Fill NaNs and select columns
        final_df = final_df.fillna(0)
        
        cols = ['SliceNumber', 'FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID'] + subtypes
        final_df = final_df[cols].astype({s: int for s in subtypes + ['SliceNumber']})

        # 6. Save updated CSV
        csv_path = os.path.join(base_dir, study_id, f"{study_id}.csv")
        final_df.to_csv(csv_path, index=False)

    print("Sorting and slice numbering complete.")

if __name__ == "__main__":
    sort_slices_by_z()
