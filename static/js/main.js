// static/js/main.js
// Yeast Protein Arginine Methylation Database - Main JavaScript

// Global variables
let currentSearchResults = [];
let currentProteinData = null;

// ========== UTILITY FUNCTIONS ==========

/**
 * Show loading spinner
 */
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading" style="display: block;"><div class="spinner"></div><p>Loading...</p></div>';
    }
}

/**
 * Hide loading spinner
 */
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const loadingDiv = element.querySelector('.loading');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

/**
 * Truncate text to specified length
 */
function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '300px';
    notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ========== SEARCH FUNCTIONS ==========

/**
 * Perform protein search
 */
function searchProteins(query, searchType = 'all') {
    if (!query || query.length < 2) {
        showNotification('Please enter at least 2 characters', 'warning');
        return Promise.resolve([]);
    }
    
    return $.ajax({
        url: '/api/search',
        method: 'GET',
        data: { q: query, type: searchType },
        dataType: 'json'
    }).catch(function(error) {
        console.error('Search error:', error);
        showNotification('Search failed. Please try again.', 'danger');
        return [];
    });
}

/**
 * Display search results in table
 */
function displaySearchResults(results, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No proteins found matching your search.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-success" style="margin-bottom: 1rem;">
            Found ${results.length} protein(s)
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>ORF ID</th>
                    <th>Gene Name</th>
                    <th>Protein Name</th>
                    <th>Description</th>
                    <th>Sites</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    results.forEach(function(protein) {
        html += `
            <tr>
                <td><strong>${escapeHtml(protein.orf_id)}</strong></td>
                <td>${escapeHtml(protein.gene_name)}</td>
                <td>${escapeHtml(protein.protein_name || '-')}</td>
                <td>${escapeHtml(truncateText(protein.description, 80)) || '-'}</td>
                <td><span class="badge badge-primary">${protein.site_count || 0}</span></td>
                <td><a href="/protein/${protein.orf_id}" class="btn btn-primary btn-sm">View Details</a></td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

// ========== PROTEIN DETAIL FUNCTIONS ==========

/**
 * Load protein details
 */
function loadProteinDetails(orfId, containerId) {
    showLoading(containerId);
    
    return $.ajax({
        url: `/api/protein/${orfId}`,
        method: 'GET',
        dataType: 'json'
    }).then(function(data) {
        hideLoading(containerId);
        return data;
    }).catch(function(error) {
        hideLoading(containerId);
        console.error('Error loading protein:', error);
        document.getElementById(containerId).innerHTML = '<div class="alert alert-danger">Failed to load protein data. Please try again.</div>';
        return null;
    });
}

/**
 * Display protein details
 */
function displayProteinDetails(protein, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!protein || protein.error) {
        container.innerHTML = '<div class="alert alert-danger">Protein data not available.</div>';
        return;
    }
    
    // Build external links
    const sgdLink = `https://www.yeastgenome.org/locus/${protein.orf_id}`;
    const uniprotLink = protein.swiss_prot_acc ? `https://www.uniprot.org/uniprot/${protein.swiss_prot_acc}` : '#';
    
    // Location badges
    let locationHtml = '';
    if (protein.cellular_location && protein.cellular_location.length > 0) {
        protein.cellular_location.forEach(function(loc) {
            locationHtml += `<span class="location-tag">${escapeHtml(loc)}</span>`;
        });
    } else {
        locationHtml = '<span class="text-muted">Not specified</span>';
    }
    
    // Aliases
    let aliasHtml = '';
    if (protein.aliases && protein.aliases.length > 0) {
        protein.aliases.forEach(function(alias) {
            aliasHtml += `<span class="badge badge-secondary" style="margin: 0.2rem;">${escapeHtml(alias.alias)} (${alias.type})</span>`;
        });
    } else {
        aliasHtml = '<span class="text-muted">No aliases</span>';
    }
    
    // Methylation sites table
    let sitesHtml = '';
    if (protein.methylation_sites && protein.methylation_sites.length > 0) {
        protein.methylation_sites.forEach(function(site) {
            const pubmedLink = site.pubmed_id ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${site.pubmed_id}/" target="_blank" class="badge" style="background: #007bff; color: white;">PubMed</a>` : '-';
            sitesHtml += `
                <tr>
                    <td>${escapeHtml(site.site_id)}</td>
                    <td>${site.position || 'Not reported'}</td>
                    <td><span class="badge ${site.methylation_type === 'mono' ? 'badge-mono' : 'badge-di'}">${site.methylation_type || 'N/A'}</span></td>
                    <td>${escapeHtml(site.detection_method || '-')}</td>
                    <td><span class="badge ${site.validation_type === 'experimental' ? 'badge-exp' : 'badge-comp'}">${site.validation_type}</span></td>
                    <td>${escapeHtml(site.methyltransferase || '-')}</td>
                    <td>${site.confidence_score || '-'}</td>
                    <td><span class="badge badge-info">${site.source_id}</span></td>
                    <td>${pubmedLink}</td>
                </tr>
            `;
        });
    } else {
        sitesHtml = '<tr><td colspan="9" style="text-align: center;">No methylation sites reported</td></tr>';
    }
    
    const html = `
        <div class="card">
            <h1>${escapeHtml(protein.gene_name)} (${escapeHtml(protein.orf_id)})</h1>
            <p style="font-size: 1.1rem; color: var(--text-muted);">${escapeHtml(protein.protein_name || '')}</p>
            
            <div class="d-flex gap-2" style="margin: 1rem 0;">
                <a href="${sgdLink}" target="_blank" class="btn btn-primary">🔗 View on SGD</a>
                ${protein.swiss_prot_acc ? `<a href="${uniprotLink}" target="_blank" class="btn btn-secondary">🔗 View on UniProt</a>` : ''}
            </div>
            
            <h3>📄 Description</h3>
            <p>${escapeHtml(protein.description || 'No description available')}</p>
            
            <h3>📍 Cellular Location</h3>
            <div>${locationHtml}</div>
            
            <h3>🏷️ Aliases</h3>
            <div>${aliasHtml}</div>
            
            <h3>📏 Protein Details</h3>
            <ul>
                <li><strong>Sequence Length:</strong> ${protein.sequence_length || 'Unknown'} amino acids</li>
                <li><strong>Organism:</strong> ${escapeHtml(protein.organism)}</li>
            </ul>
        </div>
        
        <div class="card">
            <h2>🧬 Methylation Sites</h2>
            ${protein.sequence_length ? `<button onclick="showSequencePlot('${protein.orf_id}')" class="btn btn-secondary" style="margin-bottom: 1rem;">📊 View Sequence Position Plot</button>` : ''}
            <div id="sequence-plot" style="margin: 1rem 0;"></div>
            
            <div style="overflow-x: auto;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Site ID</th><th>Position</th><th>Type</th><th>Method</th><th>Validation</th><th>Methyltransferase</th><th>Score</th><th>Source</th><th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sitesHtml}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    currentProteinData = protein;
}

// ========== PLOT FUNCTIONS ==========

/**
 * Show sequence position plot
 */
function showSequencePlot(orfId) {
    const plotContainer = document.getElementById('sequence-plot');
    if (!plotContainer) return;
    
    plotContainer.innerHTML = '<div class="loading" style="display: block;"><div class="spinner"></div><p>Loading plot...</p></div>';
    plotContainer.innerHTML = `<img src="/api/plot/protein_sequence?orf_id=${orfId}&t=${Date.now()}" style="max-width: 100%; border-radius: 8px; border: 1px solid #ddd;" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\'alert alert-warning\'>Plot not available for this protein</div>';">`;
}

/**
 * Load and display statistics
 */
function loadStatistics(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '<div class="loading" style="display: block;"><div class="spinner"></div><p>Loading statistics...</p></div>';
    
    $.ajax({
        url: '/api/stats',
        method: 'GET',
        dataType: 'json'
    }).then(function(data) {
        const html = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">${data.protein_count}</div>
                    <div class="stat-label">Proteins</div>
                </div>
                <div class="stat-card stat-card-accent">
                    <div class="stat-number">${data.site_count}</div>
                    <div class="stat-label">Methylation Sites</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-number">${data.experimental_count}</div>
                    <div class="stat-label">Experimental Sites</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-number">${data.computational_count}</div>
                    <div class="stat-label">Computational Sites</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${data.mono_count}</div>
                    <div class="stat-label">Monomethylation</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-number">${data.di_count}</div>
                    <div class="stat-label">Dimethylation</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-number">${data.hmt1_substrates}</div>
                    <div class="stat-label">Hmt1p Substrates</div>
                </div>
            </div>
            <div style="margin-top: 1rem;">
                <h3>Data Sources</h3>
                <ul>
                    ${data.sources.map(s => `<li><strong>${s.source_id}</strong>: ${s.journal} (${s.year}) - ${s.count} methylation sites</li>`).join('')}
                </ul>
            </div>
        `;
        container.innerHTML = html;
    }).catch(function(error) {
        console.error('Stats error:', error);
        container.innerHTML = '<div class="alert alert-warning">Failed to load statistics</div>';
    });
}

// ========== DOWNLOAD FUNCTIONS ==========

/**
 * Download search results
 */
function downloadResults(query, format) {
    let url = '/api/download?';
    if (query && query.trim()) {
        url += 'q=' + encodeURIComponent(query.trim()) + '&';
    }
    url += 'format=' + (format === 'csv' ? 'csv' : 'tab');
    window.location.href = url;
    showNotification(`Downloading results in ${format.toUpperCase()} format...`, 'info');
}

// ========== AUTOCOMPLETE FUNCTIONS ==========

/**
 * Initialize autocomplete for search input
 */
function initAutocomplete(inputId, resultsContainerId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    let debounceTimer;
    
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 2) {
            document.getElementById(resultsContainerId).innerHTML = '';
            return;
        }
        
        debounceTimer = setTimeout(function() {
            $.ajax({
                url: '/api/autocomplete',
                method: 'GET',
                data: { q: query },
                dataType: 'json'
            }).then(function(data) {
                const container = document.getElementById(resultsContainerId);
                if (data.length > 0) {
                    let html = '<div style="position: absolute; background: white; border: 1px solid #ddd; border-radius: 8px; max-height: 200px; overflow-y: auto; z-index: 1000; width: ' + input.offsetWidth + 'px;">';
                    data.forEach(function(item) {
                        html += `<div style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee;" onclick="document.getElementById('${inputId}').value='${item.orf_id}'; document.getElementById('${resultsContainerId}').innerHTML=''; performSearch();">${escapeHtml(item.display)}</div>`;
                    });
                    html += '</div>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '';
                }
            });
        }, 300);
    });
    
    // Close autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target)) {
            document.getElementById(resultsContainerId).innerHTML = '';
        }
    });
}

// ========== INITIALIZATION ==========

$(document).ready(function() {
    // Initialize any autocomplete on the page
    if (document.getElementById('search-input')) {
        initAutocomplete('search-input', 'autocomplete-results');
    }
    
    // Add active class to current nav link
    const currentPath = window.location.pathname;
    $('.nav-links a').each(function() {
        const href = $(this).attr('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            $(this).addClass('active');
        }
    });
    
    console.log('Yeast Methylation Database - Ready');
});
