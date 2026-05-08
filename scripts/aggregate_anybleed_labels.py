import pandas as pd
import os

def aggregate_labels():
    print("Loading unlabel_anybleed_filenames.csv...")
    anybleed_df = pd.read_csv("unlabel_anybleed_filenames.csv")
    
    # Extract PatientID and StudyInstanceUID from filename
    # Format: PatientID_StudyInstanceUID.nii.gz
    # Example: ID_00526c11_ID_d6296de728.nii.gz
    def parse_filename(fname):
        name = fname.replace(".nii.gz", "")
        parts = name.split("_")
        if len(parts) >= 4:
            # Format is ID_xxx_ID_yyy
            patient_id = "_".join(parts[0:2])
            study_id = "_".join(parts[2:4])
            return patient_id, study_id
        return None, None

    anybleed_df[['PatientID', 'StudyInstanceUID']] = anybleed_df['filename'].apply(
        lambda x: pd.Series(parse_filename(x))
    )
    
    target_studies = anybleed_df['StudyInstanceUID'].unique()
    print(f"Target studies count: {len(target_studies)}")

    print("Loading metadata.csv...")
    # Load only necessary columns
    metadata = pd.read_csv("metadata.csv", usecols=['FileName', 'StudyInstanceUID'])
    
    # Remove .dcm extension for matching with stage_2_train.csv
    metadata['ImageID'] = metadata['FileName'].str.replace(".dcm", "", regex=False)
    
    print("Loading stage_2_train.csv...")
    train_labels = pd.read_csv("stage_2_train.csv")
    
    # Handle duplicates if any
    initial_count = len(train_labels)
    train_labels = train_labels.drop_duplicates(subset=['ID'])
    if len(train_labels) < initial_count:
        print(f"Dropped {initial_count - len(train_labels)} duplicate ID rows.")

    # Split ID into ImageID and Subtype
    train_labels[['ImageID', 'Subtype']] = train_labels['ID'].str.rsplit("_", n=1, expand=True)
    
    print("Pivoting labels...")
    # Pivot to get one row per ImageID
    pivoted_labels = train_labels.pivot(index='ImageID', columns='Subtype', values='Label')
    
    print("Merging metadata with labels...")
    # Join metadata with labels
    image_with_labels = metadata.merge(pivoted_labels, left_on='ImageID', right_index=True)
    
    print("Aggregating by StudyInstanceUID...")
    # Group by StudyInstanceUID and take max (if any slice has it, study has it)
    subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural', 'any']
    study_labels = image_with_labels.groupby('StudyInstanceUID')[subtypes].max().reset_index()
    
    print("Final merge with anybleed studies...")
    # Merge with our list of anybleed studies
    final_df = anybleed_df[['PatientID', 'StudyInstanceUID']].merge(study_labels, on='StudyInstanceUID', how='left')
    
    # Handle mismatches
    missing_studies = final_df[final_df['any'].isna()]
    if not missing_studies.empty:
        print(f"Warning: {len(missing_studies)} studies from anybleed list were not found in labels/metadata.")
        # Fill NaN with 0 or keep as NaN? User asked for 1, 0. If not found, maybe we should warn.
        final_df = final_df.fillna(0)
        final_df[subtypes] = final_df[subtypes].astype(int)
    else:
        final_df[subtypes] = final_df[subtypes].astype(int)

    output_file = "anybleed_aggregated_labels.csv"
    final_df.to_csv(output_file, index=False)
    print(f"Done! Saved to {output_file}")
    
    # Summary of mismatches
    with open("aggregation_summary.txt", "w") as f:
        f.write(f"Total target studies in anybleed list: {len(target_studies)}\n")
        f.write(f"Studies matched and aggregated: {len(target_studies) - len(missing_studies)}\n")
        f.write(f"Studies not found in labels: {len(missing_studies)}\n")
        if not missing_studies.empty:
            f.write("\nMissing studies (first 10):\n")
            f.write(missing_studies['StudyInstanceUID'].head(10).to_string())

if __name__ == "__main__":
    aggregate_labels()
