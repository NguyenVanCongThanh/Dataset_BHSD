import os
import nibabel as nib
import pandas as pd
from tqdm import tqdm

def sync_nii_to_png():
    tracking_file = "added_external_studies.csv"
    source_dir = "/mnt/d/all_EDH_studies_Exclude_BHSD"
    
    if not os.path.exists(tracking_file):
        print(f"Error: {tracking_file} not found.")
        return
        
    df_tracking = pd.read_csv(tracking_file)
    df_tracking = df_tracking[df_tracking['IsBHSD'] == False]
    
    print(f"Syncing {len(df_tracking)} NIfTI files to match PNG orientation (ARS)...")
    
    for _, row in tqdm(df_tracking.iterrows(), total=len(df_tracking)):
        filename = row['FileName']
        nii_path = os.path.join(source_dir, filename)
        
        if not os.path.exists(nii_path):
            print(f"Warning: {nii_path} not found.")
            continue
            
        try:
            nii_img = nib.load(nii_path)
            orig_axcodes = nib.orientations.aff2axcodes(nii_img.affine)
            
            # Target orientation to match current PNG (Face-Down, Neurological)
            # We use PLS (Posterior-Left-Superior) to force Face-Down in viewers
            targ_axcodes = ('P', 'L', 'S')
            
            if orig_axcodes == targ_axcodes:
                continue
                
            targ_ornt = nib.orientations.axcodes2ornt(targ_axcodes)
            orig_ornt = nib.orientations.axcodes2ornt(orig_axcodes)
            transform = nib.orientations.ornt_transform(orig_ornt, targ_ornt)
            
            nii_synced = nii_img.as_reoriented(transform)
            nib.save(nii_synced, nii_path)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    sync_nii_to_png()
