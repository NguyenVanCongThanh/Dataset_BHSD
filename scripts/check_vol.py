import nibabel as nib
import numpy as np
import os

def check_volume():
    file_path = "/mnt/d/BHSD/unlabel_2000/anybleed/ID_039bebb1_ID_0fdcfd6fbb.nii.gz"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
    
    nii = nib.load(file_path)
    data = nii.get_fdata()
    print(f"Shape: {data.shape}")
    print(f"Min: {np.min(data)}, Max: {np.max(data)}")

if __name__ == "__main__":
    check_volume()
