import os
import csv
import nibabel as nib
from constants_BHSD import * 
# ==============================
# PATH CONFIG
# ==============================
OUTPUT_DIR = os.path.expanduser("~/Dataset_BHSD/BHSD/header")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "BHSD_headers.csv")


# ==============================
# COLLECT HEADERS
# ==============================

records = []
all_keys = set()

for filename in os.listdir(GROUND_TRUTH_DIR):

    if not (filename.endswith(".nii") or filename.endswith(".nii.gz")):
        continue

    path = os.path.join(GROUND_TRUTH_DIR, filename)

    try:
        nii = nib.load(path)
        header = nii.header

        record = {"filename": filename}

        for key in header.keys():
            value = header[key]

            # convert numpy types to python
            try:
                value = value.tolist()
            except Exception:
                pass

            record[key] = value
            all_keys.add(key)

        records.append(record)

    except Exception as e:
        print(f"Error reading {filename}: {e}")


# ==============================
# SAVE CSV
# ==============================

fieldnames = ["filename"] + sorted(all_keys)

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for r in records:
        writer.writerow(r)

print(f"\nSaved header table to: {OUTPUT_FILE}")
print(f"Total files processed: {len(records)}")