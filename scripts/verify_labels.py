import os
import pandas as pd
import numpy as np
from tqdm import tqdm

def verify_and_reconstruct():
    metadata_path = "csv_files/raw/metadata.csv"
    train_labels_path = "csv_files/raw/stage_2_train.csv"
    anybleed_list_path = "csv_files/listings/unlabel_anybleed_filenames.csv"
    base_dir = "study_visualizations"
    
    # 1. Load anybleed study list
    print("Loading study list...")
    anybleed_df = pd.read_csv(anybleed_list_path)
    # Filenames are like ID_PatientID_ID_StudyInstanceUID.nii.gz or PatientID_StudyInstanceUID.nii.gz
    # The actual format in unlabel_anybleed_filenames.csv is PatientID_StudyInstanceUID.nii.gz
    # where PatientID is ID_xxxx and StudyInstanceUID is ID_xxxx.
    # Example: ID_039bebb1_ID_0fdcfd6fbb.nii.gz
    def extract_study_id(f):
        parts = f.replace('.nii.gz', '').split('_')
        # Assuming the second 'ID' starts the study ID
        # Format is likely ID_xxxx_ID_yyyy
        # So parts are ['ID', 'xxxx', 'ID', 'yyyy']
        return '_'.join(parts[2:])

    anybleed_studies = [extract_study_id(f) for f in anybleed_df['filename']]
    print(f"Total anybleed studies: {len(anybleed_studies)}")
    print(f"Sample study ID: {anybleed_studies[0]}")

    # 2. Load and pivot stage_2_train.csv
    print("Loading and pivoting training labels...")
    train_df = pd.read_csv(train_labels_path)
    # Handle duplicates in training data
    train_df = train_df.drop_duplicates(subset='ID')
    # ID is ImageID_Subtype
    train_df[['ImageID', 'Subtype']] = train_df['ID'].str.rsplit('_', n=1, expand=True)
    pivot_df = train_df.pivot(index='ImageID', columns='Subtype', values='Label')
    # ImageID in pivot_df is like ID_00003e691
    
    # 3. Load metadata
    print("Loading metadata...")
    meta_df = pd.read_csv(metadata_path, usecols=['FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID'])
    # FileName in meta_df is like ID_00003e691.dcm
    
    # 4. Filter metadata for only our studies
    print("Filtering metadata...")
    meta_df = meta_df[meta_df['StudyInstanceUID'].isin(anybleed_studies)]
    
    # 5. Filter for epidural positive studies (as previously identified)
    # Actually, the user wants me to verify ALL slice-level CSVs in study_visualizations
    existing_study_folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    print(f"Found {len(existing_study_folders)} study folders to verify.")

    subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural', 'any']

    discrepancies = 0
    updated_count = 0

    for study_id in tqdm(existing_study_folders):
        # Reconstruct ground truth for this study
        study_meta = meta_df[meta_df['StudyInstanceUID'] == study_id].copy()
        if study_meta.empty:
            print(f"Error: No metadata for study {study_id}")
            continue
            
        # Strip .dcm to match pivot index
        study_meta['ImageID'] = study_meta['FileName'].str.replace('.dcm', '', regex=False)
        
        # Merge with labels
        reconstructed = study_meta.merge(pivot_df, left_on='ImageID', right_index=True, how='left')
        
        # Sort by FileName to match our existing files
        reconstructed = reconstructed.sort_values('FileName')
        
        # Prepare the reconstructed DF columns in correct order
        recon_final = reconstructed[['FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID'] + subtypes]
        recon_final = recon_final.fillna(0).astype({s: int for s in subtypes})

        # Load existing CSV
        csv_path = os.path.join(base_dir, study_id, f"{study_id}.csv")
        if not os.path.exists(csv_path):
            print(f"Warning: CSV not found for {study_id}, creating it...")
            recon_final.to_csv(csv_path, index=False)
            updated_count += 1
            continue
            
        existing_df = pd.read_csv(csv_path)
        
        # Compare
        # We check if the labels match. We assume FileName order is the same.
        # To be safe, we'll merge and compare.
        comparison = pd.merge(existing_df, recon_final, on='FileName', suffixes=('_old', '_new'))
        
        mismatch = False
        for s in subtypes:
            if not (comparison[f"{s}_old"] == comparison[f"{s}_new"]).all():
                mismatch = True
                print(f"Mismatch found in study {study_id} for subtype {s}")
                break
        
        if mismatch:
            discrepancies += 1
            recon_final.to_csv(csv_path, index=False)
            updated_count += 1
        else:
            # Even if labels match, we might have added SeriesInstanceUID or other cols
            # Let's just overwrite with the reconstructed one to be 100% sure of the source
            recon_final.to_csv(csv_path, index=False)

    print(f"Verification complete.")
    print(f"Studies with label discrepancies: {discrepancies}")
    print(f"Total CSVs updated/overwritten: {len(existing_study_folders)}")

if __name__ == "__main__":
    verify_and_reconstruct()
