import os
import nibabel as nib
import pandas as pd
import numpy as np
from src.config import DATASET_DIR

# ====== Đường dẫn folder chứa file nii ======
folder_path = os.path.join(DATASET_DIR, 'ct_scans')

rows = []

for filename in os.listdir(folder_path):
    if filename.endswith(".nii"):
        
        file_path = os.path.join(folder_path, filename)
        
        # Lấy patient number (049 từ 049.nii)
        patient_id = os.path.splitext(filename)[0]
        
        img = nib.load(file_path)
        header = img.header
        
        row = {}
        row["patient_id"] = patient_id
        
        for key in header.keys():
            value = header[key]
            
            # Giữ nguyên array nhưng convert sang list cho CSV đọc được
            if isinstance(value, np.ndarray):
                value = value.tolist()
            
            # decode bytes
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="ignore")
            
            row[key] = value
        
        rows.append(row)

df = pd.DataFrame(rows)
df.to_csv("headers.csv", index=False)

print("Done.")