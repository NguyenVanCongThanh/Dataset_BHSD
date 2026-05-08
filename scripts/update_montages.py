import os
import pandas as pd
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import shutil

def window_image(img, window_center, window_width):
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2
    windowed = np.clip(img, img_min, img_max)
    return windowed

def update_montages():
    base_dir = "study_visualizations"
    raw_vol_dir = "/mnt/d/BHSD/unlabel_2000/anybleed"
    
    study_ids = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    print(f"Regenerating montages for {len(study_ids)} studies...")

    subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural']
    abbr = {
        'epidural': 'EDH',
        'intraparenchymal': 'IPH',
        'intraventricular': 'IVH',
        'subarachnoid': 'SAH',
        'subdural': 'SDH'
    }

    for study_id in tqdm(study_ids):
        study_folder = os.path.join(base_dir, study_id)
        csv_path = os.path.join(study_folder, f"{study_id}.csv")
        
        if not os.path.exists(csv_path):
            continue
            
        df = pd.read_csv(csv_path)
        patient_id = df['PatientID'].iloc[0]
        
        vol_path = os.path.join(raw_vol_dir, f"{patient_id}_{study_id}.nii.gz")
        if not os.path.exists(vol_path):
            print(f"Warning: Volume not found for {study_id}")
            continue
            
        try:
            nii = nib.load(vol_path)
            data = nii.get_fdata()
            num_slices = data.shape[2]
            
            # Ensure CSV matches volume slice count
            if len(df) != num_slices:
                print(f"Mismatch in study {study_id}: CSV has {len(df)} rows, Volume has {num_slices} slices.")
                # We skip or handle? Usually we should follow the volume.
            
            cols = 5
            rows = (num_slices + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
            fig.suptitle(f"Patient: {patient_id} | Study: {study_id}", fontsize=24, y=0.98)
            
            for i in range(rows * cols):
                ax = axes.flatten()[i]
                if i < num_slices:
                    # IMPORTANT: We assume row i in sorted CSV matches slice i in volume
                    slice_data = data[:, :, i]
                    slice_windowed = window_image(slice_data, 40, 80)
                    ax.imshow(slice_windowed.T, cmap='gray', origin='lower')
                    
                    row = df.iloc[i]
                    active_labels = [abbr[s] for s in subtypes if row[s] == 1]
                    label_str = ", ".join(active_labels) if active_labels else "Negative"
                    
                    # Use SliceNumber from CSV
                    slice_num = row['SliceNumber']
                    ax.set_title(f"Slice {slice_num}: {row['FileName']}\n{label_str}", 
                                 fontsize=10, color='red' if active_labels else 'white',
                                 backgroundcolor='black')
                ax.axis('off')
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            image_path = os.path.join(study_folder, f"{study_id}_montage.png")
            plt.savefig(image_path, dpi=120)
            plt.close(fig)
            
        except Exception as e:
            print(f"Error processing {study_id}: {e}")

if __name__ == "__main__":
    update_montages()
