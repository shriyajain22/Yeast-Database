#!/usr/bin/env python3
import mariadb
import sys

DB_CONFIG = {
    'host': 'bioed-new.bu.edu',
    'port': 4253,
    'user': 'addisony',
    'password': 'addisonyam',
    'database': 'Team6'
}

def create_database():
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS Protein_Alias")
        cursor.execute("DROP TABLE IF EXISTS Methylation_Site")
        cursor.execute("DROP TABLE IF EXISTS Literature_Source")
        cursor.execute("DROP TABLE IF EXISTS Protein")
        
        cursor.execute("""
            CREATE TABLE Literature_Source (
                source_id VARCHAR(10) PRIMARY KEY,
                citation VARCHAR(255) NOT NULL,
                journal VARCHAR(100) NOT NULL,
                year YEAR NOT NULL,
                method VARCHAR(100),
                pubmed_id VARCHAR(15),
                organism VARCHAR(100) NOT NULL DEFAULT 'S. cerevisiae'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE Protein (
                orf_id VARCHAR(20) PRIMARY KEY,
                gene_name VARCHAR(50),
                swiss_prot_acc VARCHAR(15),
                protein_name VARCHAR(100),
                description TEXT,
                cellular_location VARCHAR(50),
                seq_length INT,
                organism VARCHAR(100) NOT NULL DEFAULT 'S. cerevisiae',
		sequence TEXT
            )
        """)
        cursor.execute("CREATE INDEX idx_protein_gene_name ON Protein(gene_name)")
        cursor.execute("CREATE INDEX idx_protein_orf_id ON Protein(orf_id)")
        
        cursor.execute("""
            CREATE TABLE Methylation_Site (
                site_id VARCHAR(10) PRIMARY KEY,
                orf_id VARCHAR(20) NOT NULL,
                residue_type CHAR(1) NOT NULL DEFAULT 'R',
                residue_position INT,
                methylation_type ENUM('mono', 'di'),
                detection_method VARCHAR(50),
                validation_type ENUM('experimental', 'computational') NOT NULL,
                methyltransferase VARCHAR(50),
                confidence_score FLOAT,
                peptide_sequence TEXT,
                source_id VARCHAR(10) NOT NULL,
                FOREIGN KEY (orf_id) REFERENCES Protein(orf_id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES Literature_Source(source_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX idx_meth_orf_id ON Methylation_Site(orf_id)")
        cursor.execute("CREATE INDEX idx_meth_source ON Methylation_Site(source_id)")
        
        cursor.execute("""
            CREATE TABLE Protein_Alias (
                alias_id VARCHAR(10) PRIMARY KEY,
                orf_id VARCHAR(20) NOT NULL,
                alias VARCHAR(100) NOT NULL,
                FOREIGN KEY (orf_id) REFERENCES Protein(orf_id) ON DELETE CASCADE,
                INDEX idx_alias (alias)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tables created successfully.")
        
    except mariadb.Error as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_database()
