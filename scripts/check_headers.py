import csv
import os

data_dir = 'data'
files = ['literature_sources.csv', 'proteins.csv', 'methylation_sites.csv', 'protein_aliases.csv']

for f in files:
    path = os.path.join(data_dir, f)
    with open(path, 'r') as file:
        reader = csv.DictReader(file)
        print(f"{f}: {reader.fieldnames}")
