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

def create_visualizations():
    study_csv_dir = "csv_files/study_level_epidural"
    raw_vol_dir = "/mnt/d/BHSD/unlabel_2000/anybleed"
    output_base_dir = "study_visualizations"
    os.makedirs(output_base_dir, exist_ok=True)
    
    csv_files = [f for f in os.listdir(study_csv_dir) if f.endswith(".csv")]
    print(f"Found {len(csv_files)} study CSVs.")

    for csv_name in tqdm(csv_files):
        study_id = csv_name.replace(".csv", "")
        csv_path = os.path.join(study_csv_dir, csv_name)
        
        # Load CSV to get PatientID
        df = pd.read_csv(csv_path)
        if df.empty:
            continue
        patient_id = df['PatientID'].iloc[0]
        
        # Construct volume path
        vol_path = os.path.join(raw_vol_dir, f"{patient_id}_{study_id}.nii.gz")
        
        if not os.path.exists(vol_path):
            print(f"Warning: Volume for study {study_id} not found at {vol_path}")
            continue
            
        # Create output folder for this study
        study_output_dir = os.path.join(output_base_dir, study_id)
        os.makedirs(study_output_dir, exist_ok=True)
        
        # Copy CSV
        shutil.copy(csv_path, study_output_dir)
        
        # Load and visualize volume
        try:
            nii = nib.load(vol_path)
            data = nii.get_fdata() # (H, W, Slices)
            num_slices = data.shape[2]
            
            # Create grid
            cols = 5
            rows = (num_slices + cols - 1) // cols
            
            # Increase figure size for 5 columns
            fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
            fig.suptitle(f"Patient: {patient_id} | Study: {study_id}", fontsize=24, y=0.98)
            
            subtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural']
            # Abbreviation mapping
            abbr = {
                'epidural': 'EDH',
                'intraparenchymal': 'IPH',
                'intraventricular': 'IVH',
                'subarachnoid': 'SAH',
                'subdural': 'SDH'
            }

            for i in range(rows * cols):
                ax = axes.flatten()[i]
                if i < num_slices:
                    slice_data = data[:, :, i]
                    # Apply brain window
                    slice_windowed = window_image(slice_data, 40, 80)
                    ax.imshow(slice_windowed.T, cmap='gray', origin='lower')
                    
                    # Get labels from CSV
                    row = df.iloc[i]
                    active_labels = [abbr[s] for s in subtypes if row[s] == 1]
                    label_str = ", ".join(active_labels) if active_labels else "Negative"
                    
                    ax.set_title(f"Slice {i}: {row['FileName']}\n{label_str}", 
                                 fontsize=10, color='red' if active_labels else 'white',
                                 backgroundcolor='black')
                ax.axis('off')
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            image_path = os.path.join(study_output_dir, f"{study_id}_montage.png")
            plt.savefig(image_path, dpi=120)
            plt.close(fig)
            
        except Exception as e:
            print(f"Error processing study {study_id}: {e}")

    print(f"Visualizations created in {output_base_dir}")

if __name__ == "__main__":
    create_visualizations()
