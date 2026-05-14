import nibabel as nib
import pandas as pd
import os

df = pd.read_csv('added_external_studies.csv')
df = df[df['IsBHSD']==False]
source_dir = '/mnt/d/all_EDH_studies_Exclude_BHSD'

for f in df['FileName']:
    p = os.path.join(source_dir, f)
    if os.path.exists(p):
        nii = nib.load(p)
        print(f"{f}: {nib.orientations.aff2axcodes(nii.affine)}")
    else:
        print(f"{f}: NOT FOUND")
