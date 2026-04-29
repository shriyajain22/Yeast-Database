#!/usr/bin/env python3
"""
Yeast Protein Arginine Methylation Database
BF768 Spring 2026 - Team 6
"""

from flask import Flask, render_template, request, jsonify, send_file, make_response
import pymysql
import io
import csv
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'bioed-new.bu.edu',
    'port': 4253,
    'user': 'addisony',
    'password': 'addisonyam',
    'database': 'Team6'
}


def get_db_connection():
    """Create database connection using pymysql."""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        cursorclass=pymysql.cursors.Cursor
    )


LOCATION_MAP = {
    'C': 'Cytoplasm',
    'N': 'Nucleus',
    'Nu': 'Nucleolus',
    'M': 'Membrane',
    'Mt': 'Mitochondria',
    'P': 'Peroxisome',
    'V': 'Vacuole'
}


@app.route('/')
def index():
    """Home page."""
    return render_template('yeast_db.html')


@app.route('/api/search')
def api_search():
    """Search proteins by ORF ID or gene name."""
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT p.orf_id, p.gene_name, p.protein_name, p.description,
               COUNT(ms.site_id) as site_count
        FROM Protein p
        LEFT JOIN Methylation_Site ms ON p.orf_id = ms.orf_id
        WHERE p.orf_id LIKE %s OR p.gene_name LIKE %s
        GROUP BY p.orf_id, p.gene_name, p.protein_name, p.description
        LIMIT 30
    """

    cursor.execute(sql, (f'%{query}%', f'%{query}%'))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    proteins = []
    for row in results:
        proteins.append({
            'orf_id': row[0],
            'gene_name': row[1] or row[0],
            'protein_name': row[2] or '',
            'description': row[3][:150] + '...' if row[3] and len(row[3]) > 150 else row[3],
            'site_count': row[4] or 0
        })

    return jsonify(proteins)


@app.route('/api/protein/<orf_id>')
def api_protein_detail(orf_id):
    """Get complete protein information including methylation sites."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT orf_id, gene_name, swiss_prot_acc, protein_name,
               description, cellular_location, seq_length, organism
        FROM Protein
        WHERE orf_id = %s
    """, (orf_id,))

    protein = cursor.fetchone()

    if not protein:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Protein not found'}), 404

    locations = []
    if protein[5]:
        for loc in protein[5].split(','):
            if loc.strip() in LOCATION_MAP:
                locations.append(LOCATION_MAP[loc.strip()])

    cursor.execute("""
        SELECT ms.site_id, ms.residue_position, ms.methylation_type,
               ms.detection_method, ms.validation_type, ms.methyltransferase,
               ms.confidence_score, ls.source_id, ls.citation, ls.journal, ls.year,
               ls.pubmed_id
        FROM Methylation_Site ms
        JOIN Literature_Source ls ON ms.source_id = ls.source_id
        WHERE ms.orf_id = %s
        ORDER BY ls.year DESC, ms.residue_position
    """, (orf_id,))

    sites = cursor.fetchall()

    cursor.execute("""
        SELECT alias
        FROM Protein_Alias
        WHERE orf_id = %s
    """, (orf_id,))

    aliases = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'orf_id': protein[0],
        'gene_name': protein[1] or protein[0],
        'swiss_prot_acc': protein[2],
        'protein_name': protein[3] or '',
        'description': protein[4] or 'No description available',
        'cellular_location': locations,
        'cellular_location_raw': protein[5],
        'sequence_length': protein[6],
        'organism': protein[7],
        'methylation_sites': [{
            'site_id': s[0],
            'position': s[1],
            'methylation_type': s[2] or 'not specified',
            'detection_method': s[3],
            'validation_type': s[4],
            'methyltransferase': s[5] or 'unknown',
            'confidence_score': s[6],
            'source_id': s[7],
            'citation': s[8],
            'journal': s[9],
            'year': s[10],
            'pubmed_id': s[11]
        } for s in sites],
        'aliases': [{'alias': a[0]} for a in aliases]
    })


@app.route('/api/protein/<orf_id>/sequence')
def api_protein_sequence(orf_id):
    """Get protein sequence with highlighted methylation sites."""
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_orf = orf_id.strip().upper()

    cursor.execute("""
        SELECT `sequence`
        FROM Protein
        WHERE UPPER(TRIM(orf_id)) = %s
    """, (clean_orf,))

    result = cursor.fetchone()

    if not result or not result[0]:
        cursor.close()
        conn.close()
        return jsonify({'error': f'Sequence not available for {clean_orf}'}), 404

    sequence = result[0]

    cursor.execute("""
        SELECT residue_position, methylation_type
        FROM Methylation_Site
        WHERE UPPER(TRIM(orf_id)) = %s
          AND residue_position IS NOT NULL
        ORDER BY residue_position
    """, (clean_orf,))

    methylation_sites = cursor.fetchall()

    cursor.close()
    conn.close()

    methylated_positions = [
        int(pos) for pos, mtype in methylation_sites if pos is not None
    ]

    return jsonify({
        'orf_id': clean_orf,
        'sequence': sequence,
        'length': len(sequence),
        'methylated_positions': methylated_positions,
        'methylation_sites': [
            {'position': int(pos), 'type': mtype}
            for pos, mtype in methylation_sites
            if pos is not None
        ]
    })


@app.route('/api/stats')
def api_stats():
    """Get database statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Protein")
    protein_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Methylation_Site")
    site_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT validation_type, COUNT(*)
        FROM Methylation_Site
        GROUP BY validation_type
    """)

    validation_counts = {}
    for row in cursor.fetchall():
        validation_counts[row[0]] = row[1]

    cursor.execute("""
        SELECT methylation_type, COUNT(*)
        FROM Methylation_Site
        WHERE methylation_type IS NOT NULL
        GROUP BY methylation_type
    """)

    methylation_counts = {}
    for row in cursor.fetchall():
        methylation_counts[row[0]] = row[1]

    cursor.execute("""
        SELECT ls.source_id, ls.journal, ls.year, COUNT(*) as count
        FROM Methylation_Site ms
        JOIN Literature_Source ls ON ms.source_id = ls.source_id
        GROUP BY ls.source_id, ls.journal, ls.year
        ORDER BY ls.year
    """)

    sources = []
    for row in cursor.fetchall():
        sources.append({
            'source_id': row[0],
            'journal': row[1],
            'year': row[2],
            'count': row[3]
        })

    cursor.execute("""
        SELECT COUNT(DISTINCT p.orf_id)
        FROM Protein p
        JOIN Methylation_Site ms ON p.orf_id = ms.orf_id
        WHERE ms.methyltransferase = 'Hmt1p'
    """)

    hmt1_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({
        'protein_count': protein_count,
        'site_count': site_count,
        'experimental_count': validation_counts.get('experimental', 0),
        'computational_count': validation_counts.get('computational', 0),
        'mono_count': methylation_counts.get('mono', 0),
        'di_count': methylation_counts.get('di', 0),
        'sources': sources,
        'hmt1_substrates': hmt1_count
    })


@app.route('/api/sources')
def api_sources():
    """Return list of literature sources."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT source_id, citation, journal, year, method, pubmed_id, organism
        FROM Literature_Source
        ORDER BY year
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    sources = []
    for row in rows:
        sources.append({
            'source_id': row[0],
            'citation': row[1],
            'journal': row[2],
            'year': row[3],
            'method': row[4],
            'pubmed_id': row[5],
            'organism': row[6]
        })

    return jsonify(sources)


@app.route('/api/plot/sites_per_protein')
def plot_sites_per_protein():
    """Generate cleaner bar chart of methylation sites per protein."""
    limit = request.args.get('limit', 15, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(p.gene_name, p.orf_id) as name,
               p.orf_id,
               COUNT(ms.site_id) as site_count
        FROM Protein p
        JOIN Methylation_Site ms ON p.orf_id = ms.orf_id
        GROUP BY p.orf_id, p.gene_name
        ORDER BY site_count DESC, name ASC
        LIMIT %s
    """, (limit,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        return "No data", 404

    names = [r[0] for r in results]
    counts = [r[2] for r in results]

    fig, ax = plt.subplots(figsize=(11, 6.5))

    colors = plt.cm.Blues(np.linspace(0.45, 0.80, len(counts)))
    bars = ax.barh(names, counts, color=colors, edgecolor="white", linewidth=1.2)

    ax.invert_yaxis()
    ax.set_xlabel("Number of Methylation Sites", fontsize=11, fontweight="bold")
    ax.set_ylabel("")
    ax.set_title(
        "Proteins with Most Arginine Methylation Sites",
        fontsize=14,
        fontweight="bold",
        pad=14
    )

    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    max_count = max(counts)
    ax.set_xlim(0, max_count + 1.2)

    for bar, count in zip(bars, counts):
        ax.text(
            count + 0.08,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#1f2937"
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")

    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", labelsize=9)

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=140, bbox_inches="tight")
    plt.close()
    img.seek(0)

    return send_file(img, mimetype="image/png")


@app.route('/api/plot/confidence_scores')
def plot_confidence_scores():
    """Generate cleaner bar chart of Mascot confidence scores."""
    limit = request.args.get('limit', 15, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(p.gene_name, p.orf_id) as name,
               ms.confidence_score, p.orf_id
        FROM Methylation_Site ms
        JOIN Protein p ON ms.orf_id = p.orf_id
        WHERE ms.confidence_score IS NOT NULL
        ORDER BY ms.confidence_score DESC
        LIMIT %s
    """, (limit,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        return "No data", 404

    names = [r[0] for r in results]
    scores = [r[1] for r in results]

    fig, ax = plt.subplots(figsize=(11, 6.5))

    colors = plt.cm.YlGnBu(np.linspace(0.35, 0.85, len(scores)))
    bars = ax.barh(names, scores, color=colors, edgecolor="white", linewidth=1.2)

    ax.invert_yaxis()
    ax.set_xlabel("Mascot Confidence Score", fontsize=11, fontweight="bold")
    ax.set_ylabel("")
    ax.set_title(
        "Proteins with Highest Mascot Confidence Scores",
        fontsize=14,
        fontweight="bold",
        pad=14
    )

    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    max_score = max(scores)
    ax.set_xlim(0, max_score + 45)

    for bar, score in zip(bars, scores):
        ax.text(
            score + 5,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.0f}",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#1f2937"
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")

    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", labelsize=9)

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=140, bbox_inches="tight")
    plt.close()
    img.seek(0)

    return send_file(img, mimetype="image/png")


@app.route('/api/plot/methylation_comparison')
def plot_methylation_comparison():
    """Generate clean methylation type pie chart without label overlap."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT methylation_type, COUNT(*)
        FROM Methylation_Site
        WHERE methylation_type IS NOT NULL
        GROUP BY methylation_type
    """)

    meth_counts = {}
    for row in cursor.fetchall():
        meth_counts[row[0]] = row[1]

    cursor.close()
    conn.close()

    labels = []
    sizes = []
    colors = []

    if 'mono' in meth_counts:
        labels.append('Monomethylation')
        sizes.append(meth_counts['mono'])
        colors.append('#60a5fa')

    if 'di' in meth_counts:
        labels.append('Dimethylation')
        sizes.append(meth_counts['di'])
        colors.append('#f59e0b')

    if not sizes:
        return "No data", 404

    fig, ax = plt.subplots(figsize=(7.5, 6.3))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        counterclock=False,
        explode=[0.025] * len(sizes),
        wedgeprops={
            "edgecolor": "white",
            "linewidth": 2
        },
        textprops={
            "fontsize": 11,
            "fontweight": "bold"
        }
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(11)
        autotext.set_fontweight("bold")

    ax.set_title(
        "Methylation Type Distribution",
        fontsize=15,
        fontweight="bold",
        pad=16
    )

    ax.legend(
        wedges,
        [f"{label}: {count}" for label, count in zip(labels, sizes)],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        frameon=False,
        fontsize=10,
        title="Type Count",
        title_fontsize=10
    )

    ax.axis("equal")

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=140, bbox_inches="tight")
    plt.close()
    img.seek(0)

    return send_file(img, mimetype="image/png")


@app.route('/api/plot/protein_sequence')
def plot_protein_sequence():
    """Generate sequence position plot for a protein."""
    orf_id = request.args.get('orf_id', '')

    if not orf_id:
        return "No protein specified", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT gene_name, seq_length
        FROM Protein
        WHERE orf_id = %s
    """, (orf_id,))

    protein = cursor.fetchone()

    if not protein or not protein[1]:
        cursor.close()
        conn.close()
        return "Protein length not available", 404

    gene_name = protein[0] or orf_id
    seq_len = protein[1]

    cursor.execute("""
        SELECT residue_position, methylation_type
        FROM Methylation_Site
        WHERE orf_id = %s AND residue_position IS NOT NULL
        ORDER BY residue_position
    """, (orf_id,))

    sites = cursor.fetchall()

    cursor.close()
    conn.close()

    if not sites:
        return "No position data for this protein", 404

    fig, ax = plt.subplots(figsize=(12, 3))

    ax.hlines(y=0, xmin=0, xmax=seq_len, colors='#2b6cb0', linewidth=4)

    for pos, mtype in sites:
        color = '#f59e0b' if mtype == 'di' else '#60a5fa'
        marker = '^' if mtype == 'di' else 'o'

        ax.plot(
            pos,
            0,
            marker=marker,
            markersize=10,
            color=color,
            markeredgecolor='white',
            markeredgewidth=1.2
        )

    ax.set_xlim(0, seq_len * 1.02)
    ax.set_ylim(-0.5, 0.5)
    ax.set_xlabel('Amino acid position', fontsize=12)

    ax.set_title(
        f'{gene_name} ({orf_id}) - Methylated Arginine Positions\nLength: {seq_len} aa',
        fontsize=12,
        fontweight='bold'
    )

    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D(
            [0], [0],
            marker='o',
            color='w',
            markerfacecolor='#60a5fa',
            markersize=8,
            label='Monomethylation'
        ),
        Line2D(
            [0], [0],
            marker='^',
            color='w',
            markerfacecolor='#f59e0b',
            markersize=8,
            label='Dimethylation'
        )
    ]

    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=140, bbox_inches='tight')
    plt.close()
    img.seek(0)

    return send_file(img, mimetype='image/png')


@app.route('/api/download')
def download_results():
    """Download search results as CSV or tab-delimited."""
    query = request.args.get('q', '').strip()
    format_type = request.args.get('format', 'csv')

    conn = get_db_connection()
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT p.orf_id, COALESCE(p.gene_name, p.orf_id) as name,
                   p.protein_name, p.description,
                   COUNT(ms.site_id) as site_count,
                   GROUP_CONCAT(DISTINCT ls.citation SEPARATOR '; ') as sources
            FROM Protein p
            LEFT JOIN Methylation_Site ms ON p.orf_id = ms.orf_id
            LEFT JOIN Literature_Source ls ON ms.source_id = ls.source_id
            WHERE p.orf_id LIKE %s OR p.gene_name LIKE %s
            GROUP BY p.orf_id, p.gene_name, p.protein_name, p.description
            LIMIT 100
        """, (f'%{query}%', f'%{query}%'))
    else:
        cursor.execute("""
            SELECT p.orf_id, COALESCE(p.gene_name, p.orf_id) as name,
                   p.protein_name, p.description,
                   COUNT(ms.site_id) as site_count,
                   GROUP_CONCAT(DISTINCT ls.citation SEPARATOR '; ') as sources
            FROM Protein p
            LEFT JOIN Methylation_Site ms ON p.orf_id = ms.orf_id
            LEFT JOIN Literature_Source ls ON ms.source_id = ls.source_id
            GROUP BY p.orf_id, p.gene_name, p.protein_name, p.description
            LIMIT 100
        """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()

    if format_type == 'csv':
        writer = csv.writer(output)

        writer.writerow([
            'ORF ID',
            'Gene Name',
            'Protein Name',
            'Description',
            'Methylation Sites',
            'Sources'
        ])

        for row in results:
            writer.writerow([
                row[0],
                row[1],
                row[2] or '',
                (row[3] or '')[:200],
                row[4] or 0,
                row[5] or ''
            ])

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=yeast_methylation_results.csv'
        return response

    output.write("ORF ID\tGene Name\tProtein Name\tDescription\tMethylation Sites\tSources\n")

    for row in results:
        output.write(
            f"{row[0]}\t{row[1]}\t{row[2] or ''}\t"
            f"{(row[3] or '')[:200]}\t{row[4] or 0}\t{row[5] or ''}\n"
        )

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=yeast_methylation_results.txt'

    return response


@app.route('/api/autocomplete')
def autocomplete():
    """Autocomplete for search box."""
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT orf_id, gene_name
        FROM Protein
        WHERE orf_id LIKE %s OR gene_name LIKE %s
        LIMIT 10
    """, (f'{query}%', f'{query}%'))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    suggestions = []
    for row in results:
        suggestions.append({
            'orf_id': row[0],
            'display': f"{row[0]} ({row[1] or 'unknown'})"
        })

    return jsonify(suggestions)


# NO if __name__ == '__main__' block - server handles this.
