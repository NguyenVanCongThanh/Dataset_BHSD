from hashlib import file_digest

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap
import nibabel as nib
import numpy as np
import pandas as pd
import os
from constants import DATASET_DIR, CT_SCANS_FODLER, MASKS_FOLDER, LABEL_FILE_NAME
from nibabel.processing import resample_to_output

def get_file_path(file_id, dataset_dir=DATASET_DIR, subfolder=CT_SCANS_FODLER):
    file_str = str(file_id)
    folder_path = os.path.join(dataset_dir, subfolder)

    # remove extension 
    if file_str.endswith(".nii"):
        file_str = file_str[:-4]

        if not file_str.isdigit():
            raise ValueError("File ID must be numeric.")

    patient_num = int(file_str)

    # file match
    for filename in os.listdir(folder_path):
        if filename.endswith(".nii"):
            name_without_ext = filename[:-4]
            if name_without_ext.isdigit() and int(name_without_ext) == patient_num:
                return os.path.join(folder_path, filename)

    raise FileNotFoundError(f"No file found for ID {file_id}")

def header_consistency_check(folder_path):
    all_key_sets = []
    file_keys = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".nii"):
            img = nib.load(os.path.join(folder_path, filename))
            header = img.header
            
            keys = set(header.keys())
            file_keys[filename] = keys
            all_key_sets.append(keys)

    first_keys = all_key_sets[0]
    has_difference = False

    for filename, keys in file_keys.items():
        if keys != first_keys:
            print(f"{filename} has different header keys")
            has_difference = True

    if not has_difference:
        print("All files have identical header keys.")

# -----------------------------
# Utilities
# -----------------------------

def load_nifti(path):
    nii = nib.load(path)
    data = nii.get_fdata()
    zooms = tuple(float(z) for z in nii.header.get_zooms())
    return data, zooms


def compute_window(window):
    if window is None:
        return None, None, "No window"

    wc, ww = window
    vmin = wc - ww / 2
    vmax = wc + ww / 2
    return vmin, vmax, f"WC={wc}, WW={ww}"


def get_mid_slices(volume):
    x_mid, y_mid, z_mid = np.array(volume.shape) // 2

    return {
        "Sagittal": volume[x_mid, :, :],
        "Coronal":  volume[:, y_mid, :],
        "Axial":    volume[:, :, z_mid],
    }


# -----------------------------
# Drawing
# -----------------------------

def draw_slice(ax, base_slice, mask_slice=None,
               aspect=1.0,
               vmin=None, vmax=None,
               mask_color="red",
               alpha=0.4):

    base_rot = np.rot90(base_slice)

    ax.imshow(
        base_rot,
        cmap="gray",
        aspect=aspect,
        vmin=vmin,
        vmax=vmax
    )

    if mask_slice is not None:
        mask_rot = np.rot90(mask_slice)
        mask_bool = mask_rot > 0
        masked = np.ma.masked_where(~mask_bool, mask_bool)

        cmap = ListedColormap([mask_color])

        ax.imshow(
            masked,
            cmap=cmap,
            alpha=alpha,
            aspect=aspect,
            vmin=0,
            vmax=1
        )

    ax.axis("off")


# -----------------------------
# Main API
# -----------------------------

def view_single(filename, window=None, overlay=False,
                mask_color="red", alpha=0.4):

    # --- Load CT ---
    ct_path = get_file_path(filename)
    data, zooms = load_nifti(ct_path)

    # --- Load mask ---
    mask_data = None
    if overlay:
        mask_path = get_file_path(filename, subfolder=MASKS_FOLDER)
        mask_data, _ = load_nifti(mask_path)

    # --- Window ---
    vmin, vmax, window_str = compute_window(window)

    # --- Slices ---
    ct_slices = get_mid_slices(data)
    mask_slices = get_mid_slices(mask_data) if overlay else None

    aspects = {
        "Sagittal": zooms[2] / zooms[1],
        "Coronal":  zooms[2] / zooms[0],
        "Axial":    zooms[1] / zooms[0],
    }

    # --- Plot ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, view_name in zip(axes, ct_slices.keys()):

        draw_slice(
            ax,
            ct_slices[view_name],
            mask_slices[view_name] if overlay else None,
            aspect=aspects[view_name],
            vmin=vmin,
            vmax=vmax,
            mask_color=mask_color,
            alpha=alpha
        )

        ax.set_title(view_name)

    # --- Metadata ---
    shape_str = f"Shape: {data.shape}"
    zoom_str = f"Voxel: {zooms[0]:.3f} x {zooms[1]:.3f} x {zooms[2]:.3f} mm"
    file_str = f"File: {os.path.basename(ct_path)}"
    overlay_str = "Mask ON" if overlay else "Mask OFF"

    fig.suptitle(
        f"{file_str}\n{shape_str}\n{zoom_str}\n{window_str}\n{overlay_str}",
        fontsize=11
    )

    plt.tight_layout()
    plt.subplots_adjust(top=0.83)
    plt.show()



def view_all(filename,
             window=None,
             overlay=False,
             mask_color="red",
             alpha=0.4,
             cols=6,
             figsize_scale=2.5, dataset_dir = DATASET_DIR, label_file_name=LABEL_FILE_NAME):

    # --- Load CT ---
    ct_path = get_file_path(filename)
    data, zooms = load_nifti(ct_path)

    # --- Load labels ---
    label_path = os.path.join(dataset_dir, label_file_name)
    df_labels = pd.read_csv(label_path)

    # Lấy patient number từ filename (ví dụ 049.nii → 49)
    patient_id = int(os.path.splitext(filename)[0])

    # --- Load mask ---
    mask_data = None
    if overlay:
        mask_path = get_file_path(filename, subfolder="masks")
        mask_data, _ = load_nifti(mask_path)

    # --- Window ---
    vmin, vmax, window_str = compute_window(window)

    # --- Axial slices ---
    n_slices = data.shape[2]
    rows = int(np.ceil(n_slices / cols))

    aspect = zooms[1] / zooms[0]

    fig, axes = plt.subplots(rows, cols,
                             figsize=(cols * figsize_scale,
                                      rows * figsize_scale))

    axes = np.array(axes).reshape(-1)

    # Các cột label
    label_columns = [
        "Intraventricular",
        "Intraparenchymal",
        "Subarachnoid",
        "Epidural",
        "Subdural",
        "No_Hemorrhage",
        "Fracture_Yes_No"
    ]

    for i in range(len(axes)):

        ax = axes[i]

        if i < n_slices:

            base_slice = data[:, :, i]
            mask_slice = mask_data[:, :, i] if overlay else None

            draw_slice(
                ax,
                base_slice,
                mask_slice,
                aspect=aspect,
                vmin=vmin,
                vmax=vmax,
                mask_color=mask_color,
                alpha=alpha
            )

            # --- Lấy label của slice ---
            slice_number = i + 1

            row = df_labels[
                (df_labels["PatientNumber"] == patient_id) &
                (df_labels["SliceNumber"] == slice_number)
            ]

            if not row.empty:
                active_labels = [
                    col for col in label_columns
                    if row.iloc[0][col] == 1
                ]
                label_text = ", ".join(active_labels) if active_labels else "None"
            else:
                label_text = "No Label"

            ax.set_title(f"#{i} | {label_text}", fontsize=7)

        else:
            ax.axis("off")

    # --- Metadata ---
    shape_str = f"Shape: {data.shape}"
    zoom_str = f"Voxel: {zooms[0]:.3f} x {zooms[1]:.3f} x {zooms[2]:.3f} mm"
    file_str = f"File: {os.path.basename(ct_path)}"
    overlay_str = "Mask ON" if overlay else "Mask OFF"

    fig.suptitle(
        f"{file_str}\n{shape_str}\n{zoom_str}\n{window_str}\n{overlay_str}",
        fontsize=12
    )

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()


############### Volume ################
def cal_mask_volume(mask_data, zooms):
    dx, dy, dz = zooms
    
    voxel_volume = dx * dy * dz  # mm³
    # print("Unique values:", np.unique(mask_data))
    num_voxels = np.sum(mask_data > 0)
    # print(num_voxels)
    
    total_volume_mm3 = num_voxels * voxel_volume
    total_volume_ml = total_volume_mm3 / 1000
    
    return total_volume_mm3, total_volume_ml

def build_volume_dataframe(dataset_dir):
    
    mask_dir = os.path.join(dataset_dir, "masks")
    mask_files = sorted([f for f in os.listdir(mask_dir) if f.endswith(".nii")])
    
    results = []
    
    for file in mask_files:
        
        mask_path = os.path.join(mask_dir, file)
        
        mask_data, zooms = load_nifti(mask_path)
        
        _, volume_ml = cal_mask_volume(mask_data, zooms)
        
        patient_id = int(os.path.splitext(file)[0])
        
        results.append({
            "PatientNumber": patient_id,
            "MaskVolume_ml": volume_ml
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values("PatientNumber").reset_index(drop=True)
    
    return df