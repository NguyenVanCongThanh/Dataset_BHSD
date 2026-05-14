import os
import pandas as pd
import nibabel as nib
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm

def apply_window(img, window_center=40, window_width=80):
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2
    img = np.clip(img, img_min, img_max)
    img = (img - img_min) / window_width * 255.0
    return img.astype(np.uint8)

def fix_external_studies():
    tracking_file = "added_external_studies.csv"
    source_dir = "/mnt/d/all_EDH_studies_Exclude_BHSD"
    target_base_dir = "study_visualizations"
    metadata_path = "csv_files/raw/metadata.csv"
    labels_path = "csv_files/raw/stage_2_train.csv"
    
    if not os.path.exists(tracking_file):
        print(f"Error: {tracking_file} not found.")
        return
        
    print("Loading source labels and metadata for re-mapping...")
    # Load and pivot labels
    labels_df = pd.read_csv(labels_path)
    labels_df['SliceID'] = labels_df['ID'].str.split('_').str[0:2].str.join('_')
    labels_df['Subtype'] = labels_df['ID'].str.split('_').str[2]
    # Drop duplicates if any before pivot
    labels_pivot = labels_df.drop_duplicates(['SliceID', 'Subtype']).pivot(index='SliceID', columns='Subtype', values='Label').reset_index()
    
    # Load metadata
    metadata_df = pd.read_csv(metadata_path)
    
    df_tracking = pd.read_csv(tracking_file)
    df_tracking = df_tracking[df_tracking['IsBHSD'] == False]
    
    print(f"Found {len(df_tracking)} external studies to fix.")
    
    for _, row in tqdm(df_tracking.iterrows(), total=len(df_tracking)):
        patient_id = row['PatientID']
        study_id = row['StudyID']
        filename = row['FileName']
        
        nii_path = os.path.join(source_dir, filename)
        if not os.path.exists(nii_path):
            print(f"Warning: {nii_path} not found.")
            continue
            
        # 1. Correct Mapping Logic
        study_meta = metadata_df[metadata_df['StudyInstanceUID'] == study_id].copy()
        if study_meta.empty:
            print(f"Warning: No metadata for {study_id}. Skipping.")
            continue
            
        # Sort by Z ascending (Inferior to Superior) to match NIfTI volume index
        study_meta['Z'] = study_meta['ImagePositionPatient'].str.strip('[]').str.split().str[2].astype(float)
        study_meta = study_meta.sort_values('Z', ascending=True)
        study_meta['SliceID'] = study_meta['FileName'].str.replace(".dcm", "", regex=False)
        
        # Merge with labels
        study_data = study_meta.merge(labels_pivot, on='SliceID', how='left').fillna(0)
        
        # Load NIfTI and reorient to LAS
        nii_img = nib.load(nii_path)
        orig_axcodes = nib.orientations.aff2axcodes(nii_img.affine)
        targ_ornt = nib.orientations.axcodes2ornt(('L', 'A', 'S'))
        orig_ornt = nib.orientations.axcodes2ornt(orig_axcodes)
        transform = nib.orientations.ornt_transform(orig_ornt, targ_ornt)
        nii_las = nii_img.as_reoriented(transform)
        
        img_vol = nii_las.get_fdata()
        count = min(img_vol.shape[2], len(study_data))
        study_data = study_data.iloc[:count]
        
        # Save corrected study CSV
        study_dir = os.path.join(target_base_dir, study_id)
        os.makedirs(study_dir, exist_ok=True)
        study_csv_path = os.path.join(study_dir, f"{study_id}.csv")
        
        # Prepare tracking info for the study CSV
        study_csv_data = []
        for i in range(count):
            row_data = study_data.iloc[i]
            study_csv_data.append({
                'SliceNumber': i + 1,
                'SliceID': row_data['SliceID'],
                'epidural': row_data['epidural'],
                'intraparenchymal': row_data['intraparenchymal'],
                'intraventricular': row_data['intraventricular'],
                'subarachnoid': row_data['subarachnoid'],
                'subdural': row_data['subdural'],
                'any': row_data['any']
            })
        pd.DataFrame(study_csv_data).to_csv(study_csv_path, index=False)
        
        # 2. Regenerate Visualizations (with 180 rotation)
        slices_dir = os.path.join(study_dir, "slices")
        os.makedirs(slices_dir, exist_ok=True)
        
        # Rescale params from metadata
        rescale_slope = study_data.iloc[0]['RescaleSlope']
        rescale_intercept = study_data.iloc[0]['RescaleIntercept']
        
        subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural']
        abbr = {'epidural': 'EDH', 'intraparenchymal': 'IPH', 'intraventricular': 'IVH', 'subarachnoid': 'SAH', 'subdural': 'SDH'}
        
        # Montage setup
        cols = 5
        rows = (count + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
        fig.suptitle(f"Patient: {patient_id} | Study: {study_id}", fontsize=24, y=0.98)
        
        for i in range(rows * cols):
            ax = axes.flatten()[i]
            if i < count:
                slice_img = img_vol[:, :, i]
                hu_slice = slice_img * rescale_slope + rescale_intercept
                windowed = apply_window(hu_slice)
                
                # Apply 180 degree rotation for both slice and montage
                fixed_orientation = np.fliplr(windowed.T)
                
                # Save slice PNG
                png_path = os.path.join(slices_dir, f"slice_{i+1}.png")
                Image.fromarray(fixed_orientation).save(png_path)
                
                # Show in montage
                ax.imshow(fixed_orientation, cmap='gray')
                
                # Add title to montage slice
                row_data = study_data.iloc[i]
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
        
    print("\nFix complete! Labels re-mapped and visualizations updated with 180 rotation.")

if __name__ == "__main__":
    fix_external_studies()
