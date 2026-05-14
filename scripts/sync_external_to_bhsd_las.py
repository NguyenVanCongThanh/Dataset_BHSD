import os
import nibabel as nib
import pandas as pd
from tqdm import tqdm

def sync_external_to_las():
    source_dir = "/mnt/d/all_EDH_studies_Exclude_BHSD"
    target_axcodes = ('L', 'A', 'S')
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory {source_dir} not found.")
        return
        
    nii_files = [f for f in os.listdir(source_dir) if f.endswith(".nii.gz")]
    print(f"Found {len(nii_files)} NIfTI files in {source_dir}")
    
    updated_count = 0
    skipped_count = 0
    
    for filename in tqdm(nii_files, desc="Syncing to LAS"):
        file_path = os.path.join(source_dir, filename)
        
        try:
            img = nib.load(file_path)
            orig_axcodes = nib.orientations.aff2axcodes(img.affine)
            
            if orig_axcodes == target_axcodes:
                skipped_count += 1
                continue
                
            # Reorient
            orig_ornt = nib.orientations.axcodes2ornt(orig_axcodes)
            targ_ornt = nib.orientations.axcodes2ornt(target_axcodes)
            transform = nib.orientations.ornt_transform(orig_ornt, targ_ornt)
            
            img_las = img.as_reoriented(transform)
            
            # Save back to same location
            nib.save(img_las, file_path)
            updated_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    print(f"\nSync Complete!")
    print(f"Updated: {updated_count} files")
    print(f"Already LAS: {skipped_count} files")

if __name__ == "__main__":
    sync_external_to_las()
