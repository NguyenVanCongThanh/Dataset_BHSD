import os
import pandas as pd
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import shutil
import json

def window_image(img, window_center, window_width):
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2
    windowed = np.clip(img, img_min, img_max)
    return windowed

def generate_html_viewer(study_id, patient_id, slices_data, output_path):
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CT Slice Viewer - {study_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }}
        .header {{
            width: 100%;
            padding: 20px;
            background-color: #1e293b;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            text-align: center;
        }}
        .viewer-container {{
            flex: 1;
            display: flex;
            flex-direction: row;
            width: 100%;
            max-width: 1200px;
            padding: 20px;
            box-sizing: border-box;
            gap: 20px;
        }}
        .image-section {{
            flex: 2;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #000;
            border-radius: 12px;
            position: relative;
            box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.5);
        }}
        #slice-img {{
            max-height: 80vh;
            max-width: 100%;
            image-rendering: pixelated;
        }}
        .info-section {{
            flex: 1;
            background-color: #1e293b;
            padding: 24px;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .label-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.875rem;
            margin-right: 8px;
            margin-bottom: 8px;
        }}
        .label-true {{ background-color: #ef4444; color: white; }}
        .label-false {{ background-color: #334155; color: #94a3b8; }}
        .control-panel {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        input[type=range] {{
            width: 100%;
            cursor: pointer;
        }}
        .nav-btns {{
            display: flex;
            gap: 10px;
        }}
        button {{
            flex: 1;
            padding: 10px;
            background-color: #3b82f6;
            border: none;
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        button:hover {{ background-color: #2563eb; }}
        .keyboard-hint {{
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0">Patient: {patient_id}</h2>
        <p style="margin:5px 0 0 0; opacity:0.7">Study: {study_id}</p>
    </div>
    
    <div class="viewer-container">
        <div class="image-section">
            <img id="slice-img" src="" alt="CT Slice">
        </div>
        
        <div class="info-section">
            <div>
                <h3 id="slice-title">Slice 1</h3>
                <p id="filename-text" style="font-family: monospace; font-size: 0.9rem; color: #94a3b8;"></p>
            </div>
            
            <div id="labels-container">
                <!-- Labels will be injected here -->
            </div>
            
            <div class="control-panel">
                <label for="slice-slider">Navigate Slices:</label>
                <input type="range" id="slice-slider" min="0" max="0" value="0">
                <div class="nav-btns">
                    <button onclick="changeSlice(-1)">Prev</button>
                    <button onclick="changeSlice(1)">Next</button>
                </div>
            </div>

            <div class="keyboard-hint">
                Use <b>Arrow Keys</b> or <b>Mouse Wheel</b> to flip slices.
            </div>
        </div>
    </div>

    <script>
        const slices = {json.dumps(slices_data)};
        let currentIndex = 0;

        const imgElement = document.getElementById('slice-img');
        const slider = document.getElementById('slice-slider');
        const titleText = document.getElementById('slice-title');
        const filenameText = document.getElementById('filename-text');
        const labelsContainer = document.getElementById('labels-container');

        slider.max = slices.length - 1;

        function updateViewer(index) {{
            currentIndex = index;
            const slice = slices[currentIndex];
            
            imgElement.src = slice.img;
            slider.value = currentIndex;
            titleText.innerText = `Slice ${{currentIndex + 1}} / ${{slices.length}}`;
            filenameText.innerText = slice.filename;
            
            // Update labels
            labelsContainer.innerHTML = '<h4>Labels:</h4>';
            const allSubtypes = ['epidural', 'intraparenchymal', 'intraventricular', 'subarachnoid', 'subdural'];
            const abbr = {{
                'epidural': 'EDH',
                'intraparenchymal': 'IPH',
                'intraventricular': 'IVH',
                'subarachnoid': 'SAH',
                'subdural': 'SDH'
            }};
            
            allSubtypes.forEach(s => {{
                const isTrue = slice.labels[s] === 1;
                const badge = document.createElement('span');
                badge.className = `label-badge ${{isTrue ? 'label-true' : 'label-false'}}`;
                badge.innerText = `${{abbr[s]}}: ${{isTrue ? 'TRUE' : 'FALSE'}}`;
                labelsContainer.appendChild(badge);
            }});
        }}

        function changeSlice(delta) {{
            let newIndex = currentIndex + delta;
            if (newIndex >= 0 && newIndex < slices.length) {{
                updateViewer(newIndex);
            }}
        }}

        slider.oninput = function() {{
            updateViewer(parseInt(this.value));
        }};

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') changeSlice(1);
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') changeSlice(-1);
        }});

        window.addEventListener('wheel', (e) => {{
            if (e.deltaY > 0) changeSlice(1);
            else changeSlice(-1);
        }});

        // Initialize
        updateViewer(0);
    </script>
</body>
</html>
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

def create_interactive_viewers():
    study_csv_dir = "csv_files/results" # Wait, I moved them to study_visualizations
    # Actually let's use the folders already in study_visualizations
    base_dir = "study_visualizations"
    raw_vol_dir = "/mnt/d/BHSD/unlabel_2000/anybleed"
    
    study_ids = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    print(f"Generating interactive viewers for {len(study_ids)} studies...")

    for study_id in tqdm(study_ids):
        study_folder = os.path.join(base_dir, study_id)
        csv_path = os.path.join(study_folder, f"{study_id}.csv")
        
        if not os.path.exists(csv_path):
            continue
            
        df = pd.read_csv(csv_path)
        patient_id = df['PatientID'].iloc[0]
        
        # Slices folder
        slices_dir = os.path.join(study_folder, "slices")
        os.makedirs(slices_dir, exist_ok=True)
        
        vol_path = os.path.join(raw_vol_dir, f"{patient_id}_{study_id}.nii.gz")
        if not os.path.exists(vol_path):
            continue
            
        nii = nib.load(vol_path)
        data = nii.get_fdata()
        
        slices_json = []
        
        for i in range(data.shape[2]):
            slice_filename = f"slice_{i+1}.png"
            slice_path = os.path.join(slices_dir, slice_filename)
            
            # Save individual slice if not already exists (or overwrite)
            if not os.path.exists(slice_path):
                slice_data = data[:, :, i]
                slice_windowed = window_image(slice_data, 40, 80)
                # Save using matplotlib or PIL
                plt.imsave(slice_path, slice_windowed.T, cmap='gray', origin='lower')
            
            # Prepare data for JS
            row = df.iloc[i]
            labels = {
                'epidural': int(row['epidural']),
                'intraparenchymal': int(row['intraparenchymal']),
                'intraventricular': int(row['intraventricular']),
                'subarachnoid': int(row['subarachnoid']),
                'subdural': int(row['subdural'])
            }
            slices_json.append({
                'filename': row['FileName'],
                'labels': labels,
                'img': f"slices/{slice_filename}"
            })
            
        # Generate HTML
        generate_html_viewer(study_id, patient_id, slices_json, os.path.join(study_folder, "viewer.html"))

if __name__ == "__main__":
    create_interactive_viewers()
