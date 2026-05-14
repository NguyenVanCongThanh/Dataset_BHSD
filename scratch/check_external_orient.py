import nibabel as nib
import os

path = "/mnt/d/all_EDH_studies_Exclude_BHSD/ID_00307f7a_ID_cba1ebce2b.nii.gz"
if os.path.exists(path):
    img = nib.load(path)
    axcodes = nib.orientations.aff2axcodes(img.affine)
    print(f"External Orientation (AxCodes): {axcodes}")
else:
    print("File not found")
