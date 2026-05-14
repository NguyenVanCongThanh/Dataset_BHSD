import os
import pandas as pd
from tqdm import tqdm

def repair_study_csvs():
    base_dir = "study_visualizations"
    metadata_path = "csv_files/raw/metadata.csv"
    
    print(f"Loading metadata from {metadata_path}...")
    meta_df = pd.read_csv(metadata_path, usecols=['FileName', 'StudyInstanceUID', 'PatientID', 'SeriesInstanceUID'])
    
    # Create a mapping for easy lookup
    meta_map = {}
    for _, row in meta_df.iterrows():
        study_id = row['StudyInstanceUID']
        slice_id = row['FileName'].replace(".dcm", "")
        if study_id not in meta_map:
            meta_map[study_id] = {'PatientID': row['PatientID'], 'SeriesInstanceUID': row['SeriesInstanceUID'], 'Slices': {}}
        meta_map[study_id]['Slices'][slice_id] = row['FileName']
    
    study_ids = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("ID_")]
    
    print(f"Repairing {len(study_ids)} study CSVs...")
    for study_id in tqdm(study_ids):
        csv_path = os.path.join(base_dir, study_id, f"{study_id}.csv")
        if not os.path.exists(csv_path):
            continue
            
        df = pd.read_csv(csv_path)
        needs_update = False
        
        if 'PatientID' not in df.columns:
            if study_id in meta_map:
                df['PatientID'] = meta_map[study_id]['PatientID']
                df['StudyInstanceUID'] = study_id
                df['SeriesInstanceUID'] = meta_map[study_id]['SeriesInstanceUID']
                needs_update = True
        
        if 'FileName' not in df.columns:
            if study_id in meta_map:
                # Map FileName based on SliceID
                if 'SliceID' in df.columns:
                    df['FileName'] = df['SliceID'].map(meta_map[study_id]['Slices']).fillna("N/A")
                    needs_update = True
        
        if needs_update:
            # Reorder columns
            cols = ['SliceNumber', 'FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID'] + [c for c in df.columns if c not in ['SliceNumber', 'FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID']]
            df = df[cols]
            df.to_csv(csv_path, index=False)

if __name__ == "__main__":
    repair_study_csvs()
