#!/usr/bin/env python3
"""
Load Protein_Alias table from CSV.
Validates that orf_id exists in Protein table.
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

def load_protein_aliases(csv_file):
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM Protein_Alias")
    
    # Get valid ORF IDs
    cursor.execute("SELECT orf_id FROM Protein")
    valid_orf_ids = {row[0] for row in cursor.fetchall()}
    
    sql = "INSERT INTO Protein_Alias (alias_id, orf_id, alias) VALUES (%s, %s, %s)"
    
    rows = 0
    skipped = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"Headers found: {reader.fieldnames}")
        
        for row in reader:
            alias_id = row.get('alias_id')
            orf_id = row.get('orf_id')
            alias = clean_text(row.get('alias'))
            
            # Validate foreign key
            if orf_id not in valid_orf_ids:
                print(f"⚠️ Skipping alias '{alias}': ORF ID '{orf_id}' not found in Protein table")
                skipped += 1
                continue
            
            try:
                cursor.execute(sql, (alias_id, orf_id, alias))
                rows += 1
            except mariadb.Error as e:
                print(f"⚠️ Error inserting {alias_id}: {e}")
                skipped += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {rows} rows into Protein_Alias (skipped {skipped})")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'protein_aliases.csv')
    
    load_protein_aliases(csv_file)
