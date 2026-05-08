import os
import pandas as pd
from tqdm import tqdm

def add_series_uid():
    metadata_path = "csv_files/raw/metadata.csv"
    base_dir = "study_visualizations"
    
    print("Loading metadata...")
    # Only load necessary columns to save memory
    metadata = pd.read_csv(metadata_path, usecols=['FileName', 'StudyInstanceUID', 'SeriesInstanceUID'])
    
    # Create a mapping of FileName -> SeriesInstanceUID for quick lookup
    # Note: FileName in metadata.csv might or might not have .dcm extension
    # Let's check first few rows
    print(f"Metadata sample:\n{metadata.head()}")
    
    study_ids = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    print(f"Updating {len(study_ids)} study CSVs...")

    for study_id in tqdm(study_ids):
        csv_path = os.path.join(base_dir, study_id, f"{study_id}.csv")
        if not os.path.exists(csv_path):
            continue
            
        study_df = pd.read_csv(csv_path)
        
        # Filter metadata for this study to be safe and faster
        study_metadata = metadata[metadata['StudyInstanceUID'] == study_id]
        
        if study_metadata.empty:
            print(f"Warning: No metadata found for study {study_id}")
            continue
            
        # Check if 1 study = 1 series
        unique_series = study_metadata['SeriesInstanceUID'].unique()
        if len(unique_series) > 1:
            print(f"Study {study_id} has multiple series: {unique_series}")
            # Map by FileName
            mapping = dict(zip(study_metadata['FileName'], study_metadata['SeriesInstanceUID']))
            study_df['SeriesInstanceUID'] = study_df['FileName'].map(mapping)
        else:
            # Simple assignment
            study_df['SeriesInstanceUID'] = unique_series[0]
            
        # Move SeriesInstanceUID after StudyInstanceUID for better readability
        cols = list(study_df.columns)
        if 'SeriesInstanceUID' in cols:
            idx = cols.index('StudyInstanceUID')
            cols.insert(idx + 1, cols.pop(cols.index('SeriesInstanceUID')))
            study_df = study_df[cols]
            
        study_df.to_csv(csv_path, index=False)

    print("Update complete.")

if __name__ == "__main__":
    add_series_uid()
