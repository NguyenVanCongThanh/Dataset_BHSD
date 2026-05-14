import nibabel as nib
import os
import random

def get_orient(path):
    if not os.path.exists(path): return "NOT FOUND"
    try:
        img = nib.load(path)
        return nib.orientations.aff2axcodes(img.affine)
    except:
        return "ERROR"

external_dir = "/mnt/d/all_EDH_studies_Exclude_BHSD"
bhsd_dir = "/mnt/d/BHSD/unlabel_2000/anybleed"

external_files = [f for f in os.listdir(external_dir) if f.endswith(".nii.gz")]
bhsd_files = [f for f in os.listdir(bhsd_dir) if f.endswith(".nii.gz")]

print("--- EXTERNAL STUDIES (Sample 5) ---")
for f in random.sample(external_files, min(5, len(external_files))):
    print(f"{f}: {get_orient(os.path.join(external_dir, f))}")

print("\n--- BHSD STUDIES (Sample 5) ---")
for f in random.sample(bhsd_files, min(5, len(bhsd_files))):
    print(f"{f}: {get_orient(os.path.join(bhsd_dir, f))}")
