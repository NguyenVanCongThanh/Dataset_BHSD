import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import pydicom
import cv2
import seaborn as sns
import nibabel as nib
import ast
import random
# from utils import get_file_path,header_consistency_check, view_single, view_all, cal_mask_volume
# utils in ./src/utils.py while this file is in ./notebooks/ so we need to import from src.utils
from src.utils.utils import *
from src.config import DATASET_DIR, CT_SCANS_FODLER, MASKS_FOLDER, LABEL_FILE_NAME, DATASET_DIR_BHSD, LABEL_FOLDER_BHSD, UNLABELED_FOLDER_BHSD