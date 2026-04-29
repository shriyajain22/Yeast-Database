#!/usr/bin/env python3
"""
Load Protein table from CSV.
Handles special characters, missing values, and ignores the 'sources' column.
"""

import mariadb
import csv
import sys
import os
import unicodedata

DB_CONFIG = {
    'host': 'bioed-new.bu.edu',
    'port': 4253,
    'user': 'addisony',
    'password': 'addisonyam',
    'database': 'Team6'
}

def clean_text(s):
    """Remove non-ASCII characters."""
    if s is None:
        return None
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')
    return s.strip() if s.strip() else None

def load_proteins(csv_file):
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM Protein")
    
    sql = """
        INSERT INTO Protein (orf_id, gene_name, swiss_prot_acc, protein_name, description, cellular_location, seq_length, organism, sequence)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    rows = 0
    skipped = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"Headers found: {reader.fieldnames}")
        
        for row in reader:
            orf_id = row.get('orf_id')
            if not orf_id:
                skipped += 1
                continue
            
            # Handle seq_length (may be empty or decimal)
            seq_len = None
            seq_len_str = row.get('seq_length', '')
            if seq_len_str and seq_len_str.strip():
                try:
                    seq_len = int(float(seq_len_str))
                except:
                    pass
            
            try:
                cursor.execute(sql, (
                    orf_id,
                    clean_text(row.get('gene_name')),
                    clean_text(row.get('swiss_prot_acc')),
                    clean_text(row.get('protein_name')),
                    clean_text(row.get('description')),
                    clean_text(row.get('cellular_location')),
                    seq_len,
                    clean_text(row.get('organism', 'S. cerevisiae')),
		    clean_text(row.get('sequence'))
                ))
                rows += 1
            except mariadb.Error as e:
                print(f"⚠️ Error inserting {orf_id}: {e}")
                skipped += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {rows} rows into Protein (skipped {skipped})")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'proteins.csv')
    
    load_proteins(csv_file)
