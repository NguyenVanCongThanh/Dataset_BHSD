import os
import pandas as pd
import json
from tqdm import tqdm

def generate_global_viewer():
    base_dir = "study_visualizations"
    output_html = os.path.join(base_dir, "index.html")
    
    study_ids = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    print(f"Consolidating {len(study_ids)} studies into a single viewer...")

    all_data = {}

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
                'slice_num': int(row['SliceNumber']) if 'SliceNumber' in row else i,
                'filename': row['FileName'],
                'labels': labels,
                'img': f"{study_id}/slices/slice_{i}.png"
            })
            
        all_data[study_id] = {
            'patient_id': patient_id,
            'series_id': series_id,
            'slices': slices_data
        }

    # HTML Template
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global CT Study Viewer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        /* Sidebar Styles */
        .sidebar {{
            width: 320px;
            background-color: #1e293b;
            border-right: 1px solid #334155;
            display: flex;
            flex-direction: column;
        }}
        .sidebar-header {{
            padding: 20px;
            background-color: #0f172a;
            border-bottom: 1px solid #334155;
        }}
        .study-list {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}
        .study-item {{
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
            font-size: 0.85rem;
        }}
        .study-item:hover {{
            background-color: #334155;
        }}
        .study-item.active {{
            background-color: #3b82f6;
            color: white;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }}
        .study-id {{ font-weight: 600; }}
        .patient-id {{ font-size: 0.75rem; opacity: 0.7; }}

        /* Main Content Styles */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .header {{
            padding: 15px 30px;
            background-color: #1e293b;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .viewer-container {{
            flex: 1;
            display: flex;
            padding: 20px;
            gap: 20px;
            overflow: hidden;
        }}
        .image-section {{
            flex: 1.5;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #000;
            border-radius: 12px;
            position: relative;
            box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.5);
            overflow: hidden;
        }}
        #slice-img {{
            max-height: 100%;
            max-width: 100%;
            object-fit: contain;
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
            max-width: 420px;
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
        input[type=range] {{ width: 100%; cursor: pointer; }}
        .nav-btns {{ display: flex; gap: 10px; }}
        button {{
            flex: 1;
            padding: 12px;
            background-color: #3b82f6;
            border: none;
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        button:hover {{ background-color: #2563eb; }}
        .metadata-grid {{
            display: grid;
            grid-template-columns: 100px 1fr;
            gap: 5px;
            font-size: 0.85rem;
            color: #94a3b8;
        }}
        .metadata-label {{ font-weight: 600; color: #f8fafc; }}
        .keyboard-hint {{
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: auto;
            background: #0f172a;
            padding: 10px;
            border-radius: 6px;
        }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 10px; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2 style="margin:0; font-size: 1.2rem;">CT Studies</h2>
            <p style="margin:5px 0 0 0; font-size: 0.8rem; opacity: 0.6;">{len(study_ids)} Epidural Cases</p>
        </div>
        <div class="study-list" id="study-list">
            <!-- Study items will be injected here -->
        </div>
    </div>

    <div class="main-content">
        <div class="header">
            <div id="study-header-info">
                <h3 id="display-patient-id" style="margin:0; font-size: 1.1rem;">Select a study</h3>
                <p id="display-ids" style="margin:0; font-size: 0.75rem; opacity: 0.6;"></p>
            </div>
            <div id="slice-counter" style="font-weight: 600; color: #3b82f6; font-size: 1.2rem;"></div>
        </div>
        
        <div class="viewer-container">
            <div class="image-section">
                <img id="slice-img" src="" alt="Select a study to view">
            </div>
            
            <div class="info-section">
                <div>
                    <h3 id="slice-title" style="margin-top:0">Slice Information</h3>
                    <div class="metadata-grid">
                        <div class="metadata-label">File:</div>
                        <div id="filename-text">-</div>
                        <div class="metadata-label">Series UID:</div>
                        <div id="series-uid-text">-</div>
                    </div>
                </div>
                
                <div id="labels-container">
                    <!-- Labels will be injected here -->
                </div>
                
                <div class="control-panel">
                    <label for="slice-slider" style="font-size: 0.9rem; font-weight: 600;">Navigate Slices:</label>
                    <input type="range" id="slice-slider" min="0" max="0" value="0">
                    <div class="nav-btns">
                        <button onclick="changeSlice(-1)">Prev</button>
                        <button onclick="changeSlice(1)">Next</button>
                    </div>
                </div>

                <div class="keyboard-hint">
                    <b>Controls:</b><br>
                    • Arrows / Scroll: Flip Slices<br>
                    • Page Up/Down: Next/Prev Study
                </div>
            </div>
        </div>
    </div>

    <script>
        const studies = {json.dumps(all_data)};
        let currentStudyId = null;
        let currentIndex = 0;

        const studyList = document.getElementById('study-list');
        const imgElement = document.getElementById('slice-img');
        const slider = document.getElementById('slice-slider');
        const sliceCounter = document.getElementById('slice-counter');
        const titleText = document.getElementById('slice-title');
        const filenameText = document.getElementById('filename-text');
        const seriesUidText = document.getElementById('series-uid-text');
        const labelsContainer = document.getElementById('labels-container');
        const displayPatientId = document.getElementById('display-patient-id');
        const displayIds = document.getElementById('display-ids');

        // Populate Sidebar
        Object.keys(studies).forEach(id => {{
            const div = document.createElement('div');
            div.className = 'study-item';
            div.id = 'item-' + id;
            div.innerHTML = `
                <div class="study-id">${{id}}</div>
                <div class="patient-id">Patient: ${{studies[id].patient_id}}</div>
            `;
            div.onclick = () => selectStudy(id);
            studyList.appendChild(div);
        }});

        function selectStudy(id) {{
            if (currentStudyId) {{
                document.getElementById('item-' + currentStudyId).classList.remove('active');
            }}
            currentStudyId = id;
            document.getElementById('item-' + currentStudyId).classList.add('active');
            document.getElementById('item-' + currentStudyId).scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            
            displayPatientId.innerText = "Patient: " + studies[id].patient_id;
            displayIds.innerText = "Study: " + id + " | Series: " + studies[id].series_id;
            
            slider.max = studies[id].slices.length - 1;
            updateViewer(0);
        }}

        function updateViewer(index) {{
            if (!currentStudyId) return;
            currentIndex = index;
            const slice = studies[currentStudyId].slices[currentIndex];
            
            imgElement.src = slice.img;
            slider.value = currentIndex;
            sliceCounter.innerText = `Slice ${{slice.slice_num}} / ${{studies[currentStudyId].slices.length - 1}}`;
            titleText.innerText = `Slice ${{slice.slice_num}}`;
            filenameText.innerText = slice.filename;
            seriesUidText.innerText = studies[currentStudyId].series_id;
            
            // Update labels
            labelsContainer.innerHTML = '<h4 style="margin-top:0">Labels:</h4>';
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
            if (!currentStudyId) return;
            let newIndex = currentIndex + delta;
            if (newIndex >= 0 && newIndex < studies[currentStudyId].slices.length) {{
                updateViewer(newIndex);
            }}
        }}

        function changeStudy(delta) {{
            const keys = Object.keys(studies);
            let idx = keys.indexOf(currentStudyId);
            let newIdx = idx + delta;
            if (newIdx >= 0 && newIdx < keys.length) {{
                selectStudy(keys[newIdx]);
            }}
        }}

        slider.oninput = function() {{
            updateViewer(parseInt(this.value));
        }};

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') changeSlice(1);
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') changeSlice(-1);
            if (e.key === 'PageDown') changeStudy(1);
            if (e.key === 'PageUp') changeStudy(-1);
        }});

        window.addEventListener('wheel', (e) => {{
            if (e.deltaY > 0) changeSlice(1);
            else changeSlice(-1);
        }}, {{ passive: true }});

        // Initialize with first study
        const firstStudy = Object.keys(studies)[0];
        if (firstStudy) selectStudy(firstStudy);
    </script>
</body>
</html>
    """
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Global viewer generated at {output_html}")

if __name__ == "__main__":
    generate_global_viewer()
