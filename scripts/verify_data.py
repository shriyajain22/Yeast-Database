#!/usr/bin/env python3
"""
Verify data integrity after loading.
Shows row counts and checks for orphaned records.
"""

import mariadb

DB_CONFIG = {
    'host': 'bioed-new.bu.edu',
    'port': 4253,
    'user': 'addisony',
    'password': 'addisonyam',
    'database': 'Team6'
}

def verify():
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("DATA VERIFICATION REPORT")
    print("="*50)
    
    # Row counts
    tables = ['Literature_Source', 'Protein', 'Methylation_Site', 'Protein_Alias']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"📊 {table}: {count} rows")
    
    print("\n" + "-"*30)
    print("FOREIGN KEY CHECKS")
    print("-"*30)
    
    # Check methylation sites with missing proteins
    cursor.execute("""
        SELECT COUNT(*) FROM Methylation_Site ms
        LEFT JOIN Protein p ON ms.orf_id = p.orf_id
        WHERE p.orf_id IS NULL
    """)
    orphan_sites = cursor.fetchone()[0]
    print(f"🔗 Methylation_Site without Protein: {orphan_sites}")
    
    # Check methylation sites with missing sources
    cursor.execute("""
        SELECT COUNT(*) FROM Methylation_Site ms
        LEFT JOIN Literature_Source ls ON ms.source_id = ls.source_id
        WHERE ls.source_id IS NULL
    """)
    orphan_sources = cursor.fetchone()[0]
    print(f"🔗 Methylation_Site without Literature_Source: {orphan_sources}")
    
    # Check aliases with missing proteins
    cursor.execute("""
        SELECT COUNT(*) FROM Protein_Alias pa
        LEFT JOIN Protein p ON pa.orf_id = p.orf_id
        WHERE p.orf_id IS NULL
    """)
    orphan_aliases = cursor.fetchone()[0]
    print(f"🔗 Protein_Alias without Protein: {orphan_aliases}")
    
    print("\n" + "-"*30)
    print("SUMMARY STATISTICS")
    print("-"*30)
    
    # Count by validation type
    cursor.execute("""
        SELECT validation_type, COUNT(*) 
        FROM Methylation_Site 
        GROUP BY validation_type
    """)
    for row in cursor.fetchall():
        print(f"📈 {row[0]}: {row[1]} sites")
    
    # Count by source
    cursor.execute("""
        SELECT ls.source_id, COUNT(*) 
        FROM Methylation_Site ms
        JOIN Literature_Source ls ON ms.source_id = ls.source_id
        GROUP BY ls.source_id
    """)
    for row in cursor.fetchall():
        print(f"📚 {row[0]}: {row[1]} sites")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Verification complete!")

if __name__ == '__main__':
    verify()
