import os
import pandas as pd
import json
from tqdm import tqdm

def generate_global_viewer():
    base_dir = "study_visualizations"
    output_html = os.path.join(base_dir, "index.html")
    
    study_ids = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("ID_")])
    print(f"Consolidating {len(study_ids)} studies into a single viewer...")

    os.makedirs(os.path.join(base_dir, "data", "studies"), exist_ok=True)

    # Load external studies tracking if exists
    external_studies = []
    if os.path.exists("added_external_studies.csv"):
        ext_df = pd.read_csv("added_external_studies.csv")
        external_studies = ext_df['StudyID'].tolist()

    studies_list = {}
    
    for study_id in tqdm(study_ids):
        csv_path = os.path.join(base_dir, study_id, f"{study_id}.csv")
        if not os.path.exists(csv_path):
            continue
            
        df = pd.read_csv(csv_path)
        patient_id = str(df['PatientID'].iloc[0])
        series_id = str(df['SeriesInstanceUID'].iloc[0]) if 'SeriesInstanceUID' in df.columns else "N/A"
        
        slices_data = []
        for i, row in df.iterrows():
            labels = {
                'epidural': int(row['epidural']),
                'intraparenchymal': int(row['intraparenchymal']),
                'intraventricular': int(row['intraventricular']),
                'subarachnoid': int(row['subarachnoid']),
                'subdural': int(row['subdural'])
            }
            slices_data.append({
                'slice_num': int(row['SliceNumber']),
                'filename': row['FileName'],
                'labels': labels,
                'img': f"{study_id}/slices/slice_{i+1}.png"
            })
            
        study_data = {
            'patient_id': patient_id,
            'series_id': series_id,
            'slices': slices_data
        }
        
        # Save individual study data
        with open(os.path.join(base_dir, "data", "studies", f"{study_id}.json"), 'w') as f:
            json.dump(study_data, f)
            
        # Add to summary list
        is_bhsd = study_id not in external_studies
        studies_list[study_id] = {
            'patient_id': patient_id,
            'slice_count': len(slices_data),
            'is_bhsd': is_bhsd
        }

    # Save the main list
    with open(os.path.join(base_dir, "data", "studies_list.json"), 'w') as f:
        json.dump(studies_list, f)

    # Load Premium Template
    header_path = "/home/thanh/Dataset_Ana/scratch/header.html"
    footer_path = "/home/thanh/Dataset_Ana/scratch/footer.html"
    
    if os.path.exists(header_path) and os.path.exists(footer_path):
        with open(header_path, 'r') as f:
            header = f.read()
        with open(footer_path, 'r') as f:
            footer = f.read()
        
        full_html = header + footer
        
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"Global viewer regenerated. Data saved to study_visualizations/data/")

    else:
        print("Error: Premium template parts not found.")

if __name__ == "__main__":
    generate_global_viewer()
