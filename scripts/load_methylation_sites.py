#!/usr/bin/env python3
"""
Load Methylation_Site table from CSV.
Handles:
- validation_type mapping: 'comp.' -> 'computational', 'exp.' -> 'experimental'
- Empty methylation_type -> NULL
- Empty values for various fields
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

def map_validation_type(val):
    """Map CSV validation_type values to database enum."""
    if not val:
        return None
    val = val.strip().lower()
    if val == 'comp.' or val == 'comp' or val == 'computational':
        return 'computational'
    elif val == 'exp.' or val == 'exp' or val == 'experimental':
        return 'experimental'
    return val  # fallback

def load_methylation_sites(csv_file):
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM Methylation_Site")
    
    # Get valid ORF IDs and source IDs for validation
    cursor.execute("SELECT orf_id FROM Protein")
    valid_orf_ids = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT source_id FROM Literature_Source")
    valid_source_ids = {row[0] for row in cursor.fetchall()}
    
    sql = """
        INSERT INTO Methylation_Site 
        (site_id, orf_id, residue_type, residue_position, methylation_type, detection_method,
         validation_type, methyltransferase, confidence_score, peptide_sequence, source_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    rows = 0
    skipped = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"Headers found: {reader.fieldnames}")
        
        for row in reader:
            site_id = row.get('site_id')
            orf_id = row.get('orf_id')
            source_id = row.get('source_id')
            
            # Validate foreign keys
            if orf_id not in valid_orf_ids:
                print(f"⚠️ Skipping {site_id}: ORF ID '{orf_id}' not found in Protein table")
                skipped += 1
                continue
            
            if source_id not in valid_source_ids:
                print(f"⚠️ Skipping {site_id}: Source ID '{source_id}' not found in Literature_Source")
                skipped += 1
                continue
            
            # Handle position (may be empty)
            pos = None
            pos_str = row.get('residue_position', '')
            if pos_str and pos_str.strip():
                try:
                    pos = int(float(pos_str))
                except:
                    pass
            
            # Handle methylation_type - convert empty string to None
            meth_type = row.get('methylation_type', '')
            if meth_type and meth_type.strip():
                meth_type = meth_type.strip().lower()
                if meth_type not in ['mono', 'di']:
                    meth_type = None
            else:
                meth_type = None
            
            # Handle validation_type - map 'comp.' to 'computational', 'exp.' to 'experimental'
            val_type_raw = row.get('validation_type', '')
            val_type = map_validation_type(val_type_raw)
            if not val_type:
                print(f"⚠️ Skipping {site_id}: Invalid validation_type '{val_type_raw}'")
                skipped += 1
                continue
            
            # Handle confidence score (may be empty or 'null')
            conf = None
            conf_str = row.get('confidence_score', '')
            if conf_str and conf_str.strip() and conf_str.lower() != 'null':
                try:
                    conf = float(conf_str)
                except:
                    pass
            
            # Handle methyltransferase (may be empty or 'null')
            mtase = clean_text(row.get('methyltransferase'))
            if mtase and mtase.lower() == 'null':
                mtase = None
            
            # Handle detection_method (may be empty)
            detection = row.get('detection_method', '')
            if not detection or not detection.strip():
                detection = None
            
            try:
                cursor.execute(sql, (
                    site_id,
                    orf_id,
                    row.get('residue_type', 'R'),
                    pos,
                    meth_type,
                    detection,
                    val_type,
                    mtase,
                    conf,
                    None,  # peptide_sequence
                    source_id
                ))
                rows += 1
            except mariadb.Error as e:
                print(f"⚠️ Error inserting {site_id}: {e}")
                skipped += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {rows} rows into Methylation_Site (skipped {skipped})")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'methylation_sites.csv')
    
    load_methylation_sites(csv_file)
