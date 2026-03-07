import os

DATASET_ROOT = "/mnt/d/BHSD"
# DATASET_ROOT = "/mnt/c/Users/Admin/Desktop/ICH_BHSD"

LABEL_DIR = os.path.join(DATASET_ROOT, "label_192")
UNLABEL_DIR = os.path.join(DATASET_ROOT, "unlabel_2000")

ANY_BLEED_DIR = os.path.join(UNLABEL_DIR, "anybleed")
NO_BLEED_DIR = os.path.join(UNLABEL_DIR, "nobleed")

GROUND_TRUTH_DIR = os.path.join(LABEL_DIR, "ground truths")
IMAGE_DIR = os.path.join(LABEL_DIR, "images")

LABEL_COLORS = {
    1: (1, 0, 0),      # red
    2: (1, 0.5, 0),    # orange
    3: (1, 1, 0),      # yellow
    4: (0, 1, 1),      # cyan
    5: (1, 0, 1)       # magenta
}

LABEL_MAP = {
    0: "background",
    1: "EDH",
    2: "IPH",
    3: "IVH",
    4: "SAH",
    5: "SDH",
}

HEADER_CSV = "/home/thanh/Dataset/BHSD/header/BHSD_headers.csv"