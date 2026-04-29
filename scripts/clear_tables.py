#!/usr/bin/env python3
"""
Clear all data from tables without dropping them.
Useful before reloading data.
"""

import mariadb

DB_CONFIG = {
    'host': 'bioed-new.bu.edu',
    'port': 4253,
    'user': 'addisony',
    'password': 'addisonyam',
    'database': 'Team6'
}

def clear_tables():
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear in reverse order of dependencies
    tables = ['Protein_Alias', 'Methylation_Site', 'Protein', 'Literature_Source']
    
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
        print(f"✅ Cleared {table}")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    clear_tables()
