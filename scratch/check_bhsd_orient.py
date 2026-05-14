import nibabel as nib
import os

path = "/mnt/d/BHSD/unlabel_2000/anybleed/ID_00526c11_ID_d6296de728.nii.gz"
if os.path.exists(path):
    img = nib.load(path)
    axcodes = nib.orientations.aff2axcodes(img.affine)
    print(f"BHSD Orientation (AxCodes): {axcodes}")
else:
    print("File not found")
