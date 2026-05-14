import pandas as pd

# Paths
metadata_path = '/home/thanh/Dataset_Ana/csv_files/raw/metadata.csv'
train_path = '/home/thanh/Dataset_Ana/csv_files/raw/stage_2_train.csv'

print("Loading labels...")
df_train = pd.read_csv(train_path)

# Filter for epidural and label == 1
epidural_df = df_train[df_train['ID'].str.contains('_epidural') & (df_train['Label'] == 1)].copy()

# Extract SOPInstanceUID (remove _epidural)
epidural_df['SOPInstanceUID'] = epidural_df['ID'].str.replace('_epidural', '')

print(f"Number of epidural slices found: {len(epidural_df)}")

print("Loading metadata...")
# Only load necessary columns to save memory
cols = ['FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID']
df_meta = pd.read_csv(metadata_path, usecols=cols)

# Extract SOPInstanceUID from FileName (remove .dcm)
df_meta['SOPInstanceUID'] = df_meta['FileName'].str.replace('.dcm', '')

print("Merging data...")
# Merge to get Study and Series IDs for epidural slices
merged_df = pd.merge(epidural_df[['SOPInstanceUID']], df_meta, on='SOPInstanceUID')

# Get unique Study/Series combinations
# Note: The user asked for PatientID, StudyID, SerieID. 
# We'll include PatientID, StudyInstanceUID, and SeriesInstanceUID.
unique_epidural_list = merged_df[['PatientID', 'StudyInstanceUID', 'SeriesInstanceUID']].drop_duplicates()

output_csv = '/home/thanh/Dataset_Ana/csv_files/processed/epidural_studies.csv'
unique_epidural_list.to_csv(output_csv, index=False)

num_studies = unique_epidural_list['StudyInstanceUID'].nunique()
num_series = unique_epidural_list['SeriesInstanceUID'].nunique()

print("\nResults:")
print(f"Total Epidural Studies: {num_studies}")
print(f"Total Epidural Series: {num_series}")
print(f"List of epidural studies saved to: {output_csv}")
