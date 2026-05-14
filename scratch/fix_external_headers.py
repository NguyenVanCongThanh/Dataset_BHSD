import os
import nibabel as nib
from tqdm import tqdm

def sync_headers_to_bhsd(directory):
    nii_files = sorted([f for f in os.listdir(directory) if f.endswith('.nii.gz')])
    print(f"Bắt đầu chuẩn hóa {len(nii_files)} file trong {directory}...")

    for filename in tqdm(nii_files):
        filepath = os.path.join(directory, filename)
        try:
            img = nib.load(filepath)
            header = img.header
            affine = img.affine

            # Thiết lập qform và sform về cùng Code 1 (Scanner Space)
            header.set_qform(affine, code=1)
            header.set_sform(affine, code=1)

            # Lưu đè trực tiếp
            img.to_filename(filepath)
            
        except Exception as e:
            print(f"Lỗi khi xử lý {filename}: {e}")

if __name__ == "__main__":
    target_dir = "/mnt/d/all_EDH_studies_Exclude_BHSD"
    sync_headers_to_bhsd(target_dir)
