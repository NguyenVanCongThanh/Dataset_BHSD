import os
import pandas as pd
import nibabel as nib
import numpy as np
from tqdm import tqdm
import json
import argparse
from PIL import Image
import matplotlib.pyplot as plt

def apply_window(img, window_center=40, window_width=80):
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2
    img = np.clip(img, img_min, img_max)
    img = (img - img_min) / window_width * 255.0
    return img.astype(np.uint8)

def process_studies(source_dir, limit=None):
    target_base_dir = "study_visualizations"
    metadata_path = "csv_files/raw/metadata.csv"
    labels_path = "csv_files/raw/stage_2_train.csv"
    tracking_file = "added_external_studies.csv"
    
    # Load existing tracking to skip already processed
    processed_files = set()
    if os.path.exists(tracking_file):
        existing_df = pd.read_csv(tracking_file)
        processed_files = set(existing_df['FileName'].tolist())
    
    print(f"Loading metadata from {metadata_path}...")
    meta_df = pd.read_csv(metadata_path, usecols=['FileName', 'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID', 'ImagePositionPatient', 'RescaleSlope', 'RescaleIntercept'])
    
    print(f"Loading labels from {labels_path}...")
    labels_df = pd.read_csv(labels_path)
    labels_df[['SliceID', 'Diagnosis']] = labels_df['ID'].str.rsplit('_', n=1, expand=True)
    labels_df = labels_df.drop_duplicates(subset=['SliceID', 'Diagnosis'])
    
    print("Pivoting labels...")
    labels_pivot = labels_df.pivot(index='SliceID', columns='Diagnosis', values='Label').reset_index()
    
    # Get list of files in source dir
    all_nii_files = sorted([f for f in os.listdir(source_dir) if f.endswith(".nii.gz")])
    nii_files = [f for f in all_nii_files if f not in processed_files]
    
    print(f"Found {len(all_nii_files)} total files. {len(nii_files)} new files to process.")
    
    if limit:
        nii_files = nii_files[:limit]
        print(f"Limit applied: Processing only first {limit} new files.")

    added_count = 0
    new_tracking_data = []
    
    for filename in tqdm(nii_files, desc="Processing Studies"):
        # Naming format: PatientID_StudyID.nii.gz
        base_name = filename.replace(".nii.gz", "")
        last_id_idx = base_name.rfind("ID_")
        if last_id_idx <= 0: continue
        
        patient_id = base_name[:last_id_idx-1]
        study_id = base_name[last_id_idx:]

        # Filter metadata for this study
        study_meta = meta_df[meta_df['StudyInstanceUID'] == study_id].copy()
        if study_meta.empty:
            print(f"Skipping {study_id}: No metadata found.")
            continue
            
        # Sort slices by Z coordinate (Inferior to Superior)
        study_meta['Z'] = study_meta['ImagePositionPatient'].str.strip('[]').str.split().str[2].astype(float)
        study_meta = study_meta.sort_values('Z', ascending=True)

        # Map labels
        study_meta['SliceID'] = study_meta['FileName'].str.replace(".dcm", "", regex=False)
        study_data = study_meta.merge(labels_pivot, on='SliceID', how='left').fillna(0)
        
        # Load NII and force PLS orientation (Synchronized with Face-Down PNGs)
        nii_path = os.path.join(source_dir, filename)
        try:
            nii_img = nib.load(nii_path)
            orig_axcodes = nib.orientations.aff2axcodes(nii_img.affine)
            targ_axcodes = ('P', 'L', 'S')
            
            if orig_axcodes != targ_axcodes:
                orig_ornt = nib.orientations.axcodes2ornt(orig_axcodes)
                targ_ornt = nib.orientations.axcodes2ornt(targ_axcodes)
                transform = nib.orientations.ornt_transform(orig_ornt, targ_ornt)
                nii_synced = nii_img.as_reoriented(transform)
            else:
                nii_synced = nii_img

            # Enforce Header Consistency (Match BHSD standard)
            nii_synced.header.set_qform(nii_synced.affine, code=1)
            nii_synced.header.set_sform(nii_synced.affine, code=1)
            
            # Save synchronized volume
            nib.save(nii_synced, nii_path)
            img_vol = nii_synced.get_fdata()
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
            
        count = min(img_vol.shape[2], len(study_data))
        study_data = study_data.iloc[:count]
            
        # Create directories
        study_dir = os.path.join(target_base_dir, study_id)
        slices_dir = os.path.join(study_dir, "slices")
        os.makedirs(slices_dir, exist_ok=True)
        
        # Rescale parameters
        rescale_slope = float(study_data.iloc[0]['RescaleSlope']) if 'RescaleSlope' in study_data.columns else 1.0
        rescale_intercept = float(study_data.iloc[0]['RescaleIntercept']) if 'RescaleIntercept' in study_data.columns else -1024.0
        
        processed_slices = []
        for i in range(count):
            slice_img = img_vol[:, :, i]
            hu_slice = slice_img * rescale_slope + rescale_intercept
            windowed = apply_window(hu_slice, 40, 80)
            
            # With PLS orientation, the data is already aligned for Face-Down Neurological view
            fixed_orientation = windowed
            
            png_path = os.path.join(slices_dir, f"slice_{i+1}.png")
            Image.fromarray(fixed_orientation).save(png_path)
            
            row = study_data.iloc[i]
            processed_slices.append({
                'SliceNumber': i + 1,
                'FileName': row['FileName'],
                'PatientID': patient_id,
                'StudyInstanceUID': study_id,
                'SeriesInstanceUID': row['SeriesInstanceUID'] if 'SeriesInstanceUID' in row else "N/A",
                'epidural': int(row['epidural']),
                'intraparenchymal': int(row['intraparenchymal']),
                'intraventricular': int(row['intraventricular']),
                'subarachnoid': int(row['subarachnoid']),
                'subdural': int(row['subdural']),
                'any': int(row['any'])
            })
            
        # Save study CSV
        study_csv_df = pd.DataFrame(processed_slices)
        study_csv_df.to_csv(os.path.join(study_dir, f"{study_id}.csv"), index=False)

        # Generate Montage
        cols = 5
        rows = (count + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
        fig.suptitle(f"Patient: {patient_id} | Study: {study_id}", fontsize=24, y=0.98)
        
        subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural']
        abbr = {'epidural': 'EDH', 'intraparenchymal': 'IPH', 'intraventricular': 'IVH', 'subarachnoid': 'SAH', 'subdural': 'SDH'}

        for i in range(rows * cols):
            ax = axes.flatten()[i]
            if i < count:
                slice_img = img_vol[:, :, i]
                hu_slice = slice_img * rescale_slope + rescale_intercept
                windowed = apply_window(hu_slice, 40, 80)
                # Use same orientation logic as slices
                fixed_orientation = windowed
                ax.imshow(fixed_orientation, cmap='gray')
                
                row_data = study_csv_df.iloc[i]
                active_labels = [abbr[s] for s in subtypes if row_data[s] == 1]
                label_str = ", ".join(active_labels) if active_labels else "Negative"
                ax.set_title(f"Slice {i+1}\n{label_str}", 
                             fontsize=10, color='red' if active_labels else 'white',
                             backgroundcolor='black')
            ax.axis('off')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        montage_path = os.path.join(study_dir, f"{study_id}_montage.png")
        plt.savefig(montage_path, dpi=120)
        plt.close(fig)
        
        new_tracking_data.append({
            'PatientID': patient_id,
            'StudyID': study_id,
            'FileName': filename,
            'SliceCount': count,
            'IsBHSD': False
        })
        added_count += 1

    # Update tracking file
    if new_tracking_data:
        new_df = pd.DataFrame(new_tracking_data)
        if os.path.exists(tracking_file):
            final_df = pd.concat([pd.read_csv(tracking_file), new_df], ignore_index=True)
        else:
            final_df = new_df
        final_df.to_csv(tracking_file, index=False)
        print(f"\nFinished! Added {added_count} new studies. Tracking updated in {tracking_file}")
    else:
        print("\nNo new studies were processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline for adding external CT studies.")
    parser.add_argument("--source", type=str, default="/mnt/d/all_EDH_studies_Exclude_BHSD", help="Source directory containing .nii.gz files")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of new studies to process")
    
    args = parser.parse_args()
    process_studies(args.source, args.limit)
