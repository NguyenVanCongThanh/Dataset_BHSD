import os
import csv

def generate_csv(directory, output_filename):
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} does not exist.")
        return
    
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort()
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename'])
        for f in files:
            writer.writerow([f])
    
    print(f"Successfully generated {output_filename} with {len(files)} files.")

if __name__ == "__main__":
    # Define directories
    anybleed_dir = "/mnt/d/BHSD/unlabel_2000/anybleed"
    nobleed_dir = "/mnt/d/BHSD/unlabel_2000/nobleed"
    
    # Generate CSVs
    generate_csv(anybleed_dir, "unlabel_anybleed_filenames.csv")
    generate_csv(nobleed_dir, "unlabel_nobleed_filenames.csv")
