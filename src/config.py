DATASET_DIR = "/mnt/d/computed-tomography-images-for-intracranial-hemorrhage-detection-and-segmentation-1.3.1/computed-tomography-images-for-intracranial-hemorrhage-detection-and-segmentation-1.3.1"
HEADER_PATH = "/home/thanh/Dataset/data/headers.csv"
CT_SCANS_FODLER = "ct_scans"
MASKS_FOLDER = "masks"
LABEL_FILE_NAME = "hemorrhage_diagnosis_raw_ct.csv"

################# BHSD Config #################
DATASET_DIR_BHSD = "/mnt/d/BHSD"
LABEL_FOLDER_BHSD = "label_192"
UNLABELED_FOLDER_BHSD = "unlabel_2000"


LABEL_COLORS_BHSD = {
    1: (1, 0, 0),      # red
    2: (1, 0.5, 0),    # orange
    3: (1, 1, 0),      # yellow
    4: (0, 1, 1),      # cyan
    5: (1, 0, 1)       # magenta
}