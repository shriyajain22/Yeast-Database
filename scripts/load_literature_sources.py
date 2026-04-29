#!/usr/bin/env python3
"""
Load Literature_Source table from CSV.
Handles special characters and trailing spaces in headers.
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
    return s.strip()

def load_literature_sources(csv_file):
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear existing data first
    cursor.execute("DELETE FROM Literature_Source")
    
    sql = """
        INSERT INTO Literature_Source (source_id, citation, journal, year, method, pubmed_id, organism)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    rows = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"Headers found: {reader.fieldnames}")
        
        for row in reader:
            source_id = row.get('source_id') or row.get('source_idn')
            citation = clean_text(row.get('citation'))
            journal = clean_text(row.get('journal', '').strip())
            year = int(row.get('year', 0))
            method = clean_text(row.get('method'))
            pubmed = row.get('pubmed_id') if row.get('pubmed_id') else None
            organism = clean_text(row.get('organism', '').strip())
            
            cursor.execute(sql, (source_id, citation, journal, year, method, pubmed, organism))
            rows += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {rows} rows into Literature_Source")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'literature_sources.csv')
    
    load_literature_sources(csv_file)
