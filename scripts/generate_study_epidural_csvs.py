import pandas as pd
import os

def create_study_csvs():
    output_dir = "csv_files/study_level_epidural"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading aggregated labels...")
    aggregated_df = pd.read_csv("csv_files/results/anybleed_aggregated_labels.csv")
    
    # Filter for epidural == 1
    epidural_studies = aggregated_df[aggregated_df['epidural'] == 1]
    print(f"Number of studies with epidural: {len(epidural_studies)}")
    
    if len(epidural_studies) == 0:
        print("No epidural studies found. Exiting.")
        return

    print("Loading metadata...")
    metadata = pd.read_csv("csv_files/raw/metadata.csv", usecols=['FileName', 'PatientID', 'StudyInstanceUID'])
    metadata['ImageID'] = metadata['FileName'].str.replace(".dcm", "", regex=False)
    
    print("Loading stage_2_train.csv...")
    train_labels = pd.read_csv("csv_files/raw/stage_2_train.csv")
    train_labels = train_labels.drop_duplicates(subset=['ID'])
    train_labels[['ImageID', 'Subtype']] = train_labels['ID'].str.rsplit("_", n=1, expand=True)
    
    print("Pivoting labels...")
    pivoted_labels = train_labels.pivot(index='ImageID', columns='Subtype', values='Label')
    
    print("Merging metadata with labels...")
    image_with_labels = metadata.merge(pivoted_labels, left_on='ImageID', right_index=True)
    
    # Ensure columns match the requested structure (FileName + subtype columns)
    subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural', 'any']
    cols_to_keep = ['FileName', 'PatientID', 'StudyInstanceUID'] + subtypes
    
    print("Generating individual CSVs...")
    count = 0
    for _, row in epidural_studies.iterrows():
        study_id = row['StudyInstanceUID']
        study_slices = image_with_labels[image_with_labels['StudyInstanceUID'] == study_id][cols_to_keep]
        
        if not study_slices.empty:
            # Sort by FileName to keep it organized
            study_slices = study_slices.sort_values('FileName')
            
            # Save to CSV
            output_file = os.path.join(output_dir, f"{study_id}.csv")
            study_slices.to_csv(output_file, index=False)
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} studies...")

    print(f"Done! Created {count} CSV files in {output_dir}")

if __name__ == "__main__":
    create_study_csvs()
