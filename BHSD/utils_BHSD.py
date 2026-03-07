from encodings.punycode import T
import os
import sys

sys.path.append(os.path.abspath("../.."))

import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib
from matplotlib.colors import ListedColormap

from constants_BHSD import *


# ==============================
# FILE UTILITIES
# ==============================

def find_file_recursive(folder, filename):
    """
    Recursively search for a file inside a folder.
    """
    for root, _, files in os.walk(folder):
        if filename in files:
            return os.path.join(root, filename)
    return None


# ==============================
# WINDOW UTILITIES
# ==============================

def calculate_window_range(window):
    """
    Convert (WC, WW) to (vmin, vmax)
    """
    if window is None:
        return None, None, "No window"

    wc, ww = window
    vmin = wc - ww / 2
    vmax = wc + ww / 2

    return vmin, vmax, f"WC={wc}, WW={ww}"


# ==============================
# VOLUME UTILITIES
# ==============================

def get_mid_slices(volume):
    """
    Extract sagittal, coronal, and axial middle slices.
    """

    x_mid, y_mid, z_mid = np.array(volume.shape) // 2

    return {
        "Sagittal": volume[x_mid, :, :],
        "Coronal": volume[:, y_mid, :],
        "Axial": volume[:, :, z_mid],
    }


def calculate_aspect_ratios(voxel_spacing):
    """
    Compute correct aspect ratios based on voxel spacing.
    """

    return {
        "Sagittal": voxel_spacing[2] / voxel_spacing[1],
        "Coronal": voxel_spacing[2] / voxel_spacing[0],
        "Axial": voxel_spacing[1] / voxel_spacing[0],
    }


# ==============================
# DRAWING FUNCTIONS
# ==============================

def draw_slice(
    ax,
    ct_slice,
    label_slice=None,
    aspect_ratio=1.0,
    vmin=None,
    vmax=None,
    alpha=0.4
):

    ct_rot = np.rot90(ct_slice)

    ax.imshow(
        ct_rot,
        cmap="gray",
        aspect=aspect_ratio,
        vmin=vmin,
        vmax=vmax
    )

    if label_slice is not None:

        label_rot = np.rot90(label_slice)

        labels = np.unique(label_rot)
        labels = labels[labels != 0]

        for label in labels:

            if label not in LABEL_COLORS:
                continue

            color = LABEL_COLORS[label]

            label_mask = label_rot == label
            masked = np.ma.masked_where(~label_mask, label_mask)

            cmap = ListedColormap([color])

            ax.imshow(
                masked,
                cmap=cmap,
                alpha=alpha,
                aspect=aspect_ratio,
                vmin=0,
                vmax=1
            )

    ax.axis("off")


# ==============================
# LOADING FUNCTIONS
# ==============================

def load_nifti_volume(path):
    """
    Load NIfTI file and return volume + voxel spacing.
    """

    nii = nib.load(path)

    volume = nii.get_fdata()

    voxel_spacing = tuple(
        float(v) for v in nii.header.get_zooms()
    )

    return volume, voxel_spacing


def load_ct_volume(filename, base_dir=IMAGE_DIR):
    """
    Load CT volume.
    """

    file_path = find_file_recursive(base_dir, filename)

    if file_path is None:
        raise FileNotFoundError(f"Cannot find {filename}")

    volume, voxel_spacing = load_nifti_volume(file_path)

    return file_path, volume, voxel_spacing


def load_label_volume(filename):

    label_path = find_file_recursive(GROUND_TRUTH_DIR, filename)

    if label_path is None:
        return None

    label_volume, _ = load_nifti_volume(label_path)

    return label_volume


# ==============================
# VISUALIZATION FUNCTIONS
# ==============================

# def show_mid_slices(
#     filename,
#     window=None,
#     overlay=False,
#     alpha=0.4,
#     base_dir=IMAGE_DIR
# ):

#     file_path, volume, voxel_spacing = load_ct_volume(filename, base_dir)

#     label_volume = None
#     label_slices = None
#     volume_labels = set()

#     if overlay:
#         label_volume = load_label_volume(filename)

#         if label_volume is not None:
#             label_slices = get_mid_slices(label_volume)
#             volume_labels = get_volume_labels(label_volume)

#     vmin, vmax, window_str = calculate_window_range(window)

#     ct_slices = get_mid_slices(volume)

#     aspects = calculate_aspect_ratios(voxel_spacing)

#     fig, axes = plt.subplots(1, 3, figsize=(15, 5))

#     for ax, view in zip(axes, ct_slices):

#         label_slice = None
#         slice_labels = set()

#         if label_slices:
#             label_slice = label_slices.get(view)
#             slice_labels = get_slice_labels(label_slice)

#         draw_slice(
#             ax,
#             ct_slices[view],
#             label_slice,
#             aspect_ratio=aspects[view],
#             vmin=vmin,
#             vmax=vmax,
#             alpha=alpha
#         )

#         label_str = f"\n{sorted(slice_labels)}" if slice_labels else ""
#         ax.set_title(f"{view}{label_str}")

#     shape_str = f"Shape: {volume.shape}"

#     voxel_str = (
#         f"Voxel spacing: "
#         f"{voxel_spacing[0]:.3f} x "
#         f"{voxel_spacing[1]:.3f} x "
#         f"{voxel_spacing[2]:.3f} mm"
#     )

#     volume_label_str = f"Labels: {sorted(volume_labels)}" if volume_labels else ""

#     fig.suptitle(
#         f"{os.path.basename(file_path)}\n"
#         f"{shape_str}\n"
#         f"{voxel_str}\n"
#         f"{window_str}\n"
#         f"{volume_label_str}",
#         fontsize=11
#     )

#     plt.tight_layout()
#     plt.subplots_adjust(top=0.83)
#     plt.show()


# def show_all_slices(
#     filename,
#     window=None,
#     overlay=False,
#     alpha=0.4,
#     cols=5,
#     figsize_scale=2.5
# ):

#     file_path, volume, voxel_spacing = load_ct_volume(filename)

#     label_volume = load_label_volume(filename) if overlay else None

#     volume_labels = set()
#     if label_volume is not None:
#         volume_labels = get_volume_labels(label_volume)

#     vmin, vmax, window_str = calculate_window_range(window)

#     n_slices = volume.shape[2]

#     rows = int(np.ceil(n_slices / cols))

#     aspect_ratio = voxel_spacing[1] / voxel_spacing[0]

#     fig, axes = plt.subplots(
#         rows,
#         cols,
#         figsize=(cols * figsize_scale, rows * figsize_scale)
#     )

#     axes = np.array(axes).reshape(-1)

#     for i, ax in enumerate(axes):

#         if i < n_slices:

#             ct_slice = volume[:, :, i]

#             label_slice = None
#             slice_labels = set()

#             if label_volume is not None:
#                 label_slice = label_volume[:, :, i]
#                 slice_labels = get_slice_labels(label_slice)

#             draw_slice(
#                 ax,
#                 ct_slice,
#                 label_slice,
#                 aspect_ratio=aspect_ratio,
#                 vmin=vmin,
#                 vmax=vmax,
#                 alpha=alpha
#             )

#             label_str = f"\n{sorted(slice_labels)}" if slice_labels else ""
#             ax.set_title(f"Slice {i}{label_str}", fontsize=8)

#         else:
#             ax.axis("off")

#     shape_str = f"Shape: {volume.shape}"

#     voxel_str = (
#         f"Voxel spacing: "
#         f"{voxel_spacing[0]:.3f} x "
#         f"{voxel_spacing[1]:.3f} x "
#         f"{voxel_spacing[2]:.3f} mm"
#     )

#     volume_label_str = f"Labels: {sorted(volume_labels)}" if volume_labels else ""

#     fig.suptitle(
#         f"{os.path.basename(file_path)}\n"
#         f"{shape_str}\n"
#         f"{voxel_str}\n"
#         f"{window_str}\n"
#         f"{volume_label_str}",
#         fontsize=11,
#         y=1.02
#     )

#     plt.tight_layout()
#     plt.show()

def show_all_slices(filename, window=None, overlay=False, alpha=0.4, cols=5, figsize_scale=3):
    # ... (giữ nguyên phần load data) ...
    file_path, volume, voxel_spacing = load_ct_volume(filename)
    label_volume = load_label_volume(filename) if overlay else None
    vmin, vmax, window_str = calculate_window_range(window)
    n_slices = volume.shape[2]
    rows = int(np.ceil(n_slices / cols))
    aspect_ratio = voxel_spacing[1] / voxel_spacing[0]

    # TĂNG figsize và dùng gridspec_kw để giảm khoảng cách (wspace, hspace)
    fig, axes = plt.subplots(
        rows, cols, 
        figsize=(cols * figsize_scale, rows * figsize_scale),
        gridspec_kw={'wspace': 0.02, 'hspace': 0.02} # Khoảng cách cực nhỏ giữa các slice
    )
    
    axes = np.array(axes).reshape(-1)

    for i, ax in enumerate(axes):
        ax.axis("off") # Tắt trục ngay từ đầu cho tất cả các ô
        
        if i < n_slices:
            ct_slice = volume[:, :, i]
            label_slice = label_volume[:, :, i] if label_volume is not None else None
            
            draw_slice(ax, ct_slice, label_slice, aspect_ratio=aspect_ratio, 
                       vmin=vmin, vmax=vmax, alpha=alpha)

            # THAY THẾ set_title bằng ax.text để tiết kiệm không gian
            label_slice_info = get_slice_labels(label_slice) if label_volume is not None else []
            label_str = f"#{i} {list(label_slice_info) if label_slice_info else ''}"
            
            # Ghi chữ đè lên ảnh (góc trên bên trái)
            ax.text(0.05, 0.95, label_str, color='yellow', fontsize=9, 
                    transform=ax.transAxes, va='top', ha='left',
                    bbox=dict(facecolor='black', alpha=0.5, lw=0)) 

    # Cấu hình Suptitle để không đè lên ảnh
    shape_str = f"Shape: {volume.shape}"
    voxel_str = f"Voxel: {voxel_spacing[0]:.2f}x{voxel_spacing[1]:.2f}x{voxel_spacing[2]:.2f}mm"
    
    volume_label_str = f"Labels: {sorted(get_volume_labels(label_volume))}" if label_volume is not None else ""

    fig.suptitle(
        f"{os.path.basename(file_path)} | {shape_str} | {voxel_str} | {window_str} | {volume_label_str}",
        fontsize=12, fontweight='bold', y=0.98 # Đẩy sát lên trên cùng
    )

    # Căn lề thủ công để tận dụng tối đa không gian
    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.92)
    plt.show()

def show_mid_slices(
    filename, 
    window=None, 
    overlay=False, 
    alpha=0.4, 
    base_dir=IMAGE_DIR,
    figsize_scale=5
):
    # 1. Load data tương tự show_all_slices
    file_path, volume, voxel_spacing = load_ct_volume(filename, base_dir)
    label_volume = load_label_volume(filename) if overlay else None
    
    # 2. Chuẩn bị thông tin hiển thị
    vmin, vmax, window_str = calculate_window_range(window)
    ct_slices = get_mid_slices(volume)
    label_slices = get_mid_slices(label_volume) if label_volume is not None else None
    aspects = calculate_aspect_ratios(voxel_spacing)
    
    # 3. Khởi tạo Figure (3 cột cho 3 view: Axial, Sagittal, Coronal)
    fig, axes = plt.subplots(
        1, 3, 
        figsize=(3 * figsize_scale, 1 * figsize_scale),
        gridspec_kw={'wspace': 0.02, 'hspace': 0.02}
    )

    # 4. Duyệt qua từng view để vẽ
    for ax, view in zip(axes, ct_slices):
        ax.axis("off") # Tắt trục tọa độ
        
        ct_slice = ct_slices[view]
        label_slice = label_slices.get(view) if label_slices else None
        
        # Vẽ slice (CT + Overlay nếu có)
        draw_slice(
            ax, 
            ct_slice, 
            label_slice, 
            aspect_ratio=aspects[view], 
            vmin=vmin, 
            vmax=vmax, 
            alpha=alpha
        )

        # 5. Overlay text lên ảnh thay vì set_title
        slice_labels = get_slice_labels(label_slice) if label_slice is not None else set()
        label_str = f"{view.upper()}\n{list(sorted(slice_labels)) if slice_labels else ''}"
        
        ax.text(
            0.05, 0.95, label_str, 
            color='yellow', fontsize=10, fontweight='bold',
            transform=ax.transAxes, va='top', ha='left',
            bbox=dict(facecolor='black', alpha=0.5, lw=0)
        )

    # 6. Cấu hình tiêu đề tổng quát (Suptitle)
    shape_str = f"Shape: {volume.shape}"
    voxel_str = f"Voxel: {voxel_spacing[0]:.2f}x{voxel_spacing[1]:.2f}x{voxel_spacing[2]:.2f}mm"
    
    volume_labels = get_volume_labels(label_volume) if label_volume is not None else []
    volume_label_str = f"Labels: {sorted(volume_labels)}" if volume_labels else ""

    fig.suptitle(
        f"{os.path.basename(file_path)} | {shape_str} | {voxel_str} | {window_str} | {volume_label_str}",
        fontsize=12, fontweight='bold', y=0.98
    )

    # Tối ưu không gian
    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.88)
    plt.show()


def get_slice_labels(label_slice):
    """
    Return set of label names present in a slice.

    """

    if label_slice is None:
        return set()

    labels = set(np.unique(label_slice))
    labels.discard(0)  # remove background

    return {LABEL_MAP[l] for l in labels if l in LABEL_MAP}


def get_volume_labels(label_volume):
    """
    Return set of label names present in a full volume.

    """

    if label_volume is None:
        return set()

    labels = set(np.unique(label_volume))
    labels.discard(0)

    return {LABEL_MAP[l] for l in labels if l in LABEL_MAP}


def calculate_mask_volume(label_volume, voxel_spacing):
    """
    Tính thể tích các vùng xuất huyết (nhãn > 0).
    label_volume: numpy array (3D)
    voxel_spacing: tuple/list (x_spacing, y_spacing, z_spacing) mm
    """
    if label_volume is None:
        return 0.0
    
    # Tính thể tích của một voxel đơn lẻ (mm^3)
    voxel_unit_volume = np.prod(voxel_spacing)
    
    # Đếm số lượng voxel có giá trị > 0 (tất cả các loại xuất huyết)
    num_bleed_voxels = np.sum(label_volume > 0)
    
    # Tổng thể tích tính bằng mm^3
    total_volume_mm3 = num_bleed_voxels * voxel_unit_volume
    
    # Chuyển đổi sang ml (1 ml = 1000 mm^3)
    volume_ml = total_volume_mm3 / 1000.0
    
    return volume_ml

# ==============================
# EXAMPLE
# ==============================

if __name__ == "__main__":

    show_all_slices(
        "ID_0b10cbee_ID_f91d6a7cd2.nii.gz",
        window=(40, 80),
        overlay=True
    )
    ####################
    # sample_file = os.path.join(GROUND_TRUTH_DIR, "ID_02b882cc_ID_a4892e60ae.nii.gz")
    # nii = nib.load(sample_file)
    # label_volume = nii.get_fdata()
    # volume_labels = get_volume_labels(label_volume)
    # print("\nLabels in whole volume:")
    # print(volume_labels)

    # slice_index = label_volume.shape[2] // 2
    # label_slice = label_volume[:, :, slice_index]
    # slice_labels = get_slice_labels(label_slice)

    # print(f"\nLabels in slice {slice_index}:")
    # print(slice_labels)