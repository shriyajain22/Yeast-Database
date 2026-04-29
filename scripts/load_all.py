#!/usr/bin/env python3
"""
Run all load scripts in the correct order.
Handles dependencies: Literature_Source -> Protein -> Methylation_Site -> Protein_Alias
"""

import subprocess
import sys
import os

scripts = [
    'load_literature_sources.py',
    'load_proteins.py',
    'load_methylation_sites.py',
    'load_protein_aliases.py'
]

def run_script(script):
    print(f"\n{'='*50}")
    print(f"Running {script}...")
    print('='*50)
    result = subprocess.run([sys.executable, script], capture_output=False)
    return result.returncode == 0

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    
    for script in scripts:
        if not run_script(script):
            print(f"\n❌ Failed at {script}. Stopping.")
            sys.exit(1)
    
    print("\n" + "="*50)
    print("🎉 All data loaded successfully!")
    print("="*50)
