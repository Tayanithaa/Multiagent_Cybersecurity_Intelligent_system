/**
 * Sandbox Analysis Frontend
 * Handles malware submission, status tracking, and results display
 */

const API_BASE = 'http://localhost:8000';
let currentTaskId = null;

// ============================================================================
// Tab Management
// ============================================================================

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        switchTab(tabName);
    });
});

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load data for tab
    if (tabName === 'submissions') {
        loadSubmissions();
    } else if (tabName === 'stats') {
        loadStatistics();
    }
}

// ============================================================================
// File Upload
// ============================================================================

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// File input handler
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

async function handleFileUpload(file) {
    console.log('Uploading file:', file.name);
    
    // Show progress
    document.getElementById('upload-progress').style.display = 'block';
    document.getElementById('upload-result').style.display = 'none';
    document.getElementById('progress-text').textContent = 'Uploading...';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', 'demo_user');
        
        const response = await fetch(`${API_BASE}/api/sandbox/submit`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        console.log('Upload result:', result);
        
        // Hide progress
        document.getElementById('upload-progress').style.display = 'none';
        
        // Show result
        if (result.status === 'rejected') {
            showError(`File rejected: ${result.reason}`);
        } else if (result.status === 'already_analyzed') {
            showAlreadyAnalyzed(result);
        } else {
            showUploadSuccess(result);
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('upload-progress').style.display = 'none';
        showError(error.message);
    }
}

function showUploadSuccess(result) {
    document.getElementById('upload-result').style.display = 'block';
    document.getElementById('task-id').textContent = result.task_id;
    document.getElementById('upload-status').textContent = result.status;
    document.getElementById('estimated-time').textContent = result.estimated_time || 'Unknown';
    currentTaskId = result.task_id;
}

function showAlreadyAnalyzed(result) {
    document.getElementById('upload-result').style.display = 'block';
    document.getElementById('upload-result').innerHTML = `
        <h3>ℹ️ Already Analyzed</h3>
        <p>This file has already been analyzed.</p>
        <p><strong>Task ID:</strong> <span class="mono">${result.task_id}</span></p>
        <button class="btn-primary" onclick="viewResults('${result.task_id}')">View Results</button>
    `;
}

function showError(message) {
    document.getElementById('upload-result').style.display = 'block';
    document.getElementById('upload-result').innerHTML = `
        <h3>❌ Upload Failed</h3>
        <p>${message}</p>
    `;
}

async function checkStatus() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/sandbox/status/${currentTaskId}`);
        const status = await response.json();
        
        document.getElementById('upload-status').textContent = status.status;
        
        if (status.status === 'completed') {
            document.getElementById('upload-result').innerHTML += `
                <br><button class="btn-primary" onclick="viewResults('${currentTaskId}')">
                    View Analysis Results
                </button>
            `;
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}

// ============================================================================
// Submissions List
// ============================================================================

async function loadSubmissions() {
    const listElement = document.getElementById('submissions-list');
    listElement.innerHTML = '<p class="loading">Loading submissions...</p>';
    
    try {
        const statusFilter = document.getElementById('status-filter').value;
        let url = `${API_BASE}/api/sandbox/list?limit=50`;
        if (statusFilter) {
            url += `&status=${statusFilter}`;
        }
        
        const response = await fetch(url);
        const submissions = await response.json();
        
        if (submissions.length === 0) {
            listElement.innerHTML = '<p class="info-text">No submissions found</p>';
            return;
        }
        
        let html = '<table class="submissions-table"><thead><tr>';
        html += '<th>Hash</th><th>Filename</th><th>Status</th><th>Uploaded</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        submissions.forEach(sub => {
            const shortHash = sub.file_hash.substring(0, 16) + '...';
            const status = getStatusBadge(sub.status);
            const uploaded = new Date(sub.upload_timestamp).toLocaleString();
            
            html += `<tr>
                <td class="mono">${shortHash}</td>
                <td>${sub.original_filename || 'Unknown'}</td>
                <td>${status}</td>
                <td>${uploaded}</td>
                <td>
                    <button class="btn-small" onclick="viewResults('${sub.file_hash}')">View</button>
                    <button class="btn-small" onclick="viewStatus('${sub.file_hash}')">Status</button>
                </td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        listElement.innerHTML = html;
        
    } catch (error) {
        console.error('Load submissions error:', error);
        listElement.innerHTML = '<p class="error-text">Failed to load submissions</p>';
    }
}

function getStatusBadge(status) {
    const badges = {
        'queued': '<span class="badge badge-info">Queued</span>',
        'processing': '<span class="badge badge-warning">Processing</span>',
        'completed': '<span class="badge badge-success">Completed</span>',
        'failed': '<span class="badge badge-danger">Failed</span>'
    };
    return badges[status] || status;
}

async function viewStatus(taskId) {
    try {
        const response = await fetch(`${API_BASE}/api/sandbox/status/${taskId}`);
        const status = await response.json();
        
        const modalContent = `
            <h2>Submission Status</h2>
            <div class="status-details">
                <p><strong>File Hash:</strong> <span class="mono">${status.file_hash}</span></p>
                <p><strong>Status:</strong> ${getStatusBadge(status.status)}</p>
                <p><strong>Uploaded:</strong> ${new Date(status.upload_timestamp).toLocaleString()}</p>
                <p><strong>File Size:</strong> ${formatBytes(status.file_size)}</p>
                ${status.completed_timestamp ? `<p><strong>Completed:</strong> ${new Date(status.completed_timestamp).toLocaleString()}</p>` : ''}
            </div>
        `;
        
        showModal(modalContent);
    } catch (error) {
        console.error('View status error:', error);
        alert('Failed to load status');
    }
}

// ============================================================================
// Analysis Results
// ============================================================================

function searchResults() {
    const hash = document.getElementById('search-hash').value.trim();
    if (!hash) {
        alert('Please enter a file hash');
        return;
    }
    viewResults(hash);
}

async function viewResults(taskId) {
    const container = document.getElementById('analysis-results');
    container.innerHTML = '<p class="loading">Loading analysis results...</p>';
    
    // Switch to results tab
    switchTab('results');
    
    try {
        const response = await fetch(`${API_BASE}/api/sandbox/results/${taskId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                container.innerHTML = '<p class="error-text">No analysis results found. Analysis may still be in progress.</p>';
                return;
            }
            throw new Error('Failed to load results');
        }
        
        const result = await response.json();
        displayAnalysisResults(result, container);
        
    } catch (error) {
        console.error('View results error:', error);
        container.innerHTML = `<p class="error-text">Failed to load results: ${error.message}</p>`;
    }
}

function displayAnalysisResults(result, container) {
    const riskClass = getRiskClass(result.risk_score);
    const severityClass = result.severity.toLowerCase();
    
    let html = `
        <div class="analysis-header">
            <h2>Analysis Report</h2>
            <p class="mono">${result.file_hash}</p>
        </div>
        
        <div class="threat-summary ${riskClass}">
            <div class="threat-badge">
                <h3>${result.threat_category.toUpperCase()}</h3>
                <p>Confidence: ${(result.confidence * 100).toFixed(1)}%</p>
            </div>
            <div class="risk-score">
                <h3>Risk Score</h3>
                <div class="score-value ${riskClass}">${result.risk_score}/100</div>
                <p class="severity severity-${severityClass}">${result.severity}</p>
            </div>
        </div>
        
        <div class="analysis-section">
            <h3>🎯 Key Findings</h3>
            <ul>
                <li><strong>Malware Family:</strong> ${result.malware_family || 'Unknown'}</li>
                <li><strong>Attack Techniques:</strong> ${result.attack_techniques ? result.attack_techniques.join(', ') || 'None identified' : 'None'}</li>
                <li><strong>Analysis Time:</strong> ${new Date(result.analysis_timestamp).toLocaleString()}</li>
            </ul>
        </div>
    `;
    
    // IOCs
    if (result.iocs) {
        html += `
            <div class="analysis-section">
                <h3>🔍 Indicators of Compromise (IOCs)</h3>
                ${displayIOCs(result.iocs)}
            </div>
        `;
    }
    
    // Recommendations
    if (result.recommendations) {
        html += `
            <div class="analysis-section">
                <h3>💡 Recommendations</h3>
                <ul>
                    ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Behavioral Summary
    if (result.behavioral_summary) {
        html += `
            <div class="analysis-section">
                <h3>📊 Behavioral Analysis</h3>
                <pre class="code-block">${escapeHtml(result.behavioral_summary)}</pre>
            </div>
        `;
    }
    
    // ML Predictions
    if (result.ml_predictions) {
        html += `
            <div class="analysis-section">
                <h3>🤖 Machine Learning Analysis</h3>
                <ul>
                    <li><strong>EMBER Score:</strong> ${(result.ml_predictions.ember_score * 100).toFixed(1)}%</li>
                    <li><strong>MalConv Score:</strong> ${(result.ml_predictions.malconv_score * 100).toFixed(1)}%</li>
                    <li><strong>C2 Confidence:</strong> ${(result.ml_predictions.c2_confidence * 100).toFixed(1)}%</li>
                </ul>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function displayIOCs(iocs) {
    let html = '';
    
    if (iocs.ip_addresses && iocs.ip_addresses.length > 0) {
        html += '<h4>Network IOCs:</h4><ul>';
        iocs.ip_addresses.forEach(ip => {
            html += `<li><code>${ip.value}</code> (Port: ${ip.port}, ${ip.country})</li>`;
        });
        html += '</ul>';
    }
    
    if (iocs.file_paths && iocs.file_paths.length > 0) {
        html += '<h4>File IOCs:</h4><ul>';
        iocs.file_paths.slice(0, 10).forEach(file => {
            html += `<li><code>${escapeHtml(file.value)}</code> (${file.operation})</li>`;
        });
        if (iocs.file_paths.length > 10) {
            html += `<li><em>... and ${iocs.file_paths.length - 10} more files</em></li>`;
        }
        html += '</ul>';
    }
    
    if (iocs.registry_keys && iocs.registry_keys.length > 0) {
        html += '<h4>Registry IOCs:</h4><ul>';
        iocs.registry_keys.slice(0, 10).forEach(key => {
            html += `<li><code>${escapeHtml(key.value)}</code> (${key.operation})</li>`;
        });
        if (iocs.registry_keys.length > 10) {
            html += `<li><em>... and ${iocs.registry_keys.length - 10} more keys</em></li>`;
        }
        html += '</ul>';
    }
    
    return html || '<p>No IOCs identified</p>';
}

function getRiskClass(score) {
    if (score >= 80) return 'risk-critical';
    if (score >= 60) return 'risk-high';
    if (score >= 40) return 'risk-medium';
    return 'risk-low';
}

// ============================================================================
// Statistics
// ============================================================================

async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/api/sandbox/stats`);
        const stats = await response.json();
        
        // Update stat cards
        document.getElementById('stat-total').textContent = stats.total_submissions;
        document.getElementById('stat-completed').textContent = stats.completed_analyses;
        document.getElementById('stat-risk').textContent = stats.average_risk_score;
        
        // Status breakdown chart
        createStatusChart(stats.status_breakdown);
        
        // Threat categories chart
        createThreatChart(stats.threat_categories);
        
    } catch (error) {
        console.error('Load statistics error:', error);
    }
}

function createStatusChart(statusData) {
    const ctx = document.getElementById('status-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    ctx.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(statusData),
            datasets: [{
                data: Object.values(statusData),
                backgroundColor: ['#4CAF50', '#FFC107', '#2196F3', '#F44336']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Submission Status Distribution'
                }
            }
        }
    });
}

function createThreatChart(threatData) {
    const ctx = document.getElementById('threat-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    ctx.chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(threatData),
            datasets: [{
                label: 'Threat Count',
                data: Object.values(threatData),
                backgroundColor: '#E91E63'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Threat Categories'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ============================================================================
// Modal
// ============================================================================

function showModal(content) {
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('result-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('result-modal').style.display = 'none';
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('result-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};

// ============================================================================
// Utilities
// ============================================================================

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Initialize
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Sandbox viewer initialized');
    loadSubmissions();
});
