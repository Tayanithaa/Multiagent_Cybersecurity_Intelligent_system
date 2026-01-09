// Multi-Agent SOC Dashboard - JavaScript Logic
// Connects to FastAPI backend running Member 1 + Member 2 agents

const API_BASE = 'http://localhost:8000';

let allIncidents = [];
let currentTab = 'dashboard';

// Chart instances
let threatChart = null;
let confidenceChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initFileUpload();
    initFilters();
    loadDashboard();
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);
    
    document.getElementById('refresh-btn').addEventListener('click', loadDashboard);
});

// Tab switching
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    currentTab = tabName;
    
    // Load data for the tab
    if (tabName === 'incidents') {
        loadIncidents();
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/incidents?limit=1000`);
        if (!response.ok) throw new Error('Backend not available');
        
        allIncidents = await response.json();
        console.log('📊 Loaded incidents:', allIncidents.length);
        
        updateDashboardStats(allIncidents);
        updateCharts(allIncidents);
        
        if (currentTab === 'incidents') {
            displayIncidents(allIncidents);
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showNotification('Backend not available. Please start the FastAPI server.', 'error');
    }
}

// Update dashboard statistics
function updateDashboardStats(incidents) {
    console.log('📈 Updating stats for', incidents.length, 'incidents');
    
    const total = incidents.length;
    const highSeverity = incidents.filter(i => i.severity === 'HIGH').length;
    const mediumSeverity = incidents.filter(i => i.severity === 'MEDIUM').length;
    const lowSeverity = incidents.filter(i => i.severity === 'LOW').length;
    const criticalActions = incidents.filter(i => i.action_priority === 1).length;
    
    const avgConfidence = incidents.length > 0
        ? (incidents.reduce((sum, i) => sum + (i.avg_confidence || i.bert_confidence || 0), 0) / incidents.length * 100).toFixed(1)
        : 0;
    
    console.log('Stats:', { total, highSeverity, mediumSeverity, lowSeverity, criticalActions, avgConfidence });
    
    document.getElementById('total-incidents').textContent = total;
    document.getElementById('high-severity').textContent = highSeverity;
    document.getElementById('avg-confidence').textContent = `${avgConfidence}%`;
    document.getElementById('critical-actions').textContent = criticalActions;
}

// Update charts
function updateCharts(incidents) {
    // Threat Type Distribution - Donut Chart
    const threatCounts = {};
    incidents.forEach(incident => {
        const threat = incident.threat_type || incident.bert_class || 'unknown';
        threatCounts[threat] = (threatCounts[threat] || 0) + 1;
    });
    
    const threatLabels = Object.keys(threatCounts).sort((a, b) => threatCounts[b] - threatCounts[a]);
    const threatData = threatLabels.map(label => threatCounts[label]);
    
    // Professional color palette
    const colors = ['#4F46E5', '#7C3AED', '#EC4899', '#EF4444', '#F59E0B', '#10B981', '#3B82F6', '#6366F1'];
    
    if (threatChart) threatChart.destroy();
    const threatCtx = document.getElementById('threatChart').getContext('2d');
    threatChart = new Chart(threatCtx, {
        type: 'doughnut',
        data: {
            labels: threatLabels.map(l => l.replace('_', ' ').toUpperCase()),
            datasets: [{
                data: threatData,
                backgroundColor: colors.slice(0, threatLabels.length),
                borderWidth: 3,
                borderColor: '#FFFFFF',
                hoverBorderWidth: 4,
                hoverBorderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { 
                        color: '#374151',
                        font: { size: 12, weight: '500' },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    padding: 14,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    cornerRadius: 6,
                    callbacks: {
                        label: (context) => {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return ` ${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Confidence Distribution - Line Graph
    // Create bins for confidence ranges
    const bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
    const binLabels = bins.slice(0, -1).map((bin, i) => `${bin}-${bins[i + 1]}%`);
    const binCounts = new Array(bins.length - 1).fill(0);
    
    incidents.forEach(incident => {
        const conf = (incident.bert_confidence || incident.avg_confidence || 0) * 100;
        for (let i = 0; i < bins.length - 1; i++) {
            if (conf >= bins[i] && conf < bins[i + 1]) {
                binCounts[i]++;
                break;
            }
        }
    });
    
    if (confidenceChart) confidenceChart.destroy();
    const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
    confidenceChart = new Chart(confidenceCtx, {
        type: 'line',
        data: {
            labels: binLabels,
            datasets: [{
                label: 'Number of Incidents',
                data: binCounts,
                borderColor: '#4F46E5',
                backgroundColor: 'rgba(79, 70, 229, 0.08)',
                borderWidth: 3,
                pointRadius: 5,
                pointBackgroundColor: '#4F46E5',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 2,
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#4F46E5',
                pointHoverBorderWidth: 3,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    padding: 14,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    cornerRadius: 6,
                    callbacks: {
                        label: (context) => ` ${context.parsed.y} incidents`
                    }
                }
            },
            scales: {
                x: {
                    grid: { 
                        color: '#F3F4F6',
                        drawBorder: false
                    },
                    ticks: { 
                        color: '#6B7280',
                        font: { size: 11 }
                    },
                    title: {
                        display: true,
                        text: 'Confidence Range',
                        color: '#6B7280',
                        font: { size: 12, weight: '500' }
                    }
                },
                y: {
                    grid: { 
                        color: '#F3F4F6',
                        drawBorder: false
                    },
                    ticks: { 
                        color: '#6B7280',
                        font: { size: 11 },
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Number of Incidents',
                        color: '#6B7280',
                        font: { size: 12, weight: '500' }
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Load and display incidents
async function loadIncidents() {
    if (allIncidents.length === 0) {
        await loadDashboard();
    } else {
        displayIncidents(allIncidents);
    }
}

function displayIncidents(incidents) {
    const tbody = document.getElementById('incidents-body');
    tbody.innerHTML = '';
    
    if (incidents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="no-data">No incidents to display. Upload logs to analyze.</td></tr>';
        return;
    }
    
    incidents.forEach((incident, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${incident.source_ip}</code></td>
            <td><span class="badge badge-threat">${(incident.threat_type || '').replace('_', ' ').toUpperCase()}</span></td>
            <td><span class="badge badge-${incident.severity.toLowerCase()}">${incident.severity}</span></td>
            <td><span class="badge badge-count">${incident.alert_count}</span></td>
            <td><span class="badge badge-confidence">${(incident.avg_confidence * 100).toFixed(1)}%</span></td>
            <td><small>${incident.enrichment?.location || 'N/A'}</small></td>
            <td><span class="badge badge-action">${incident.recommended_action}</span></td>
            <td><span class="badge badge-priority-${incident.action_priority}">${getPriorityLabel(incident.action_priority)}</span></td>
            <td><small>${formatTimestamp(incident.timestamp)}</small></td>
            <td><button class="btn-details" onclick="showIncidentDetails(${index})">🔍 View</button></td>
        `;
        tbody.appendChild(row);
    });
}

function getPriorityLabel(priority) {
    const labels = { 1: 'Critical', 2: 'High', 3: 'Medium' };
    return labels[priority] || 'Low';
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Filters
function initFilters() {
    const severityFilter = document.getElementById('severity-filter');
    const searchInput = document.getElementById('search-input');
    
    severityFilter.addEventListener('change', applyFilters);
    searchInput.addEventListener('input', applyFilters);
}

function applyFilters() {
    const severity = document.getElementById('severity-filter').value;
    const search = document.getElementById('search-input').value.toLowerCase();
    
    let filtered = allIncidents;
    
    if (severity) {
        filtered = filtered.filter(i => i.severity === severity);
    }
    
    if (search) {
        filtered = filtered.filter(i => 
            (i.source_ip || '').toLowerCase().includes(search) ||
            (i.threat_type || '').toLowerCase().includes(search)
        );
    }
    
    displayIncidents(filtered);
}

// File upload
function initFileUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadBox = document.getElementById('upload-box');
    const uploadBtn = document.getElementById('upload-btn');
    
    fileInput.addEventListener('change', handleFileSelect);
    uploadBtn.addEventListener('click', uploadFile);
    
    // Drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('drag-over');
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });
    
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.endsWith('.csv')) {
            fileInput.files = files;
            handleFileSelect();
        }
    });
}

function handleFileSelect() {
    const file = document.getElementById('file-input').files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.csv')) {
        showNotification('Please select a CSV file', 'error');
        return;
    }
    
    document.getElementById('file-name').textContent = `${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
    document.getElementById('file-info').style.display = 'flex';
}

async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('Please select a file first', 'error');
        return;
    }
    
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const resultBox = document.getElementById('upload-result');
    
    progressContainer.style.display = 'block';
    resultBox.style.display = 'none';
    progressFill.style.width = '0%';
    
    try {
        // Simulate progress
        progressFill.style.width = '30%';
        progressText.textContent = 'Uploading file...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        progressFill.style.width = '70%';
        progressText.textContent = 'Running BERT → Correlation → TI → Response pipeline...';
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        progressFill.style.width = '100%';
        progressText.textContent = 'Analysis complete!';
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
            resultBox.style.display = 'block';
            resultBox.className = 'result-box success';
            resultBox.innerHTML = `
                <h4>✅ Analysis Complete!</h4>
                <p>File: <strong>${file.name}</strong></p>
                <p>Incidents detected: <strong>${result.incidents_count || 0}</strong></p>
                <p>Pipeline: BERT Detection → Correlation → TI Enrichment → Response Recommendations</p>
                <button class="btn-primary" onclick="switchTab('incidents')">View Incidents</button>
            `;
            
            // Reload dashboard
            loadDashboard();
            showNotification('File analyzed successfully!', 'success');
            
            // Reset upload
            fileInput.value = '';
            document.getElementById('file-info').style.display = 'none';
        }, 1000);
        
    } catch (error) {
        console.error('Upload error:', error);
        progressContainer.style.display = 'none';
        resultBox.style.display = 'block';
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `
            <h4>❌ Upload Failed</h4>
            <p>${error.message}</p>
            <p>Make sure the FastAPI backend is running on port 8000.</p>
        `;
        showNotification('Upload failed. Check backend connection.', 'error');
    }
}

// Notifications
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification show ${type}`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

// Incident Details Modal
function showIncidentDetails(incidentIndex) {
    const modal = document.getElementById('incident-modal');
    const modalBody = document.getElementById('modal-body');
    
    const incident = allIncidents[incidentIndex];
    if (!incident) {
        console.error('Incident not found at index:', incidentIndex);
        return;
    }
    
    const enrichment = incident.enrichment || {};
    
    modalBody.innerHTML = `
        <div class="modal-section">
            <h3>🎯 BERT Detection Results</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Threat Classification:</span>
                    <span class="detail-value"><strong>${(incident.threat_type || 'unknown').replace('_', ' ').toUpperCase()}</strong></span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Model Confidence:</span>
                    <span class="detail-value badge-confidence">${(incident.avg_confidence * 100).toFixed(2)}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Severity Level:</span>
                    <span class="detail-value"><span class="badge badge-${incident.severity.toLowerCase()}">${incident.severity}</span></span>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h3>🔗 Correlation Analysis</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Source IP:</span>
                    <span class="detail-value"><code>${incident.source_ip}</code></span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Alert Count:</span>
                    <span class="detail-value"><strong>${incident.alert_count}</strong> correlated events</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Affected Users:</span>
                    <span class="detail-value">${incident.users ? incident.users.join(', ') : 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">First Detected:</span>
                    <span class="detail-value">${formatTimestamp(incident.timestamp)}</span>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h3>🌐 Threat Intelligence Enrichment</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Geolocation:</span>
                    <span class="detail-value">${enrichment.location || 'Unknown'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Organization:</span>
                    <span class="detail-value">${enrichment.org || 'Unknown'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Threat Score:</span>
                    <span class="detail-value">${enrichment.threat_score ? (enrichment.threat_score * 100).toFixed(1) + '%' : 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Blacklist Status:</span>
                    <span class="detail-value ${enrichment.blacklist_status === 'Listed' ? 'text-danger' : 'text-success'}">
                        ${enrichment.blacklist_status || 'Unknown'}
                    </span>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h3>💡 Response Recommendations</h3>
            <div class="detail-grid">
                <div class="detail-item full-width">
                    <span class="detail-label">Recommended Action:</span>
                    <span class="detail-value"><strong>${incident.recommended_action}</strong></span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Action Priority:</span>
                    <span class="detail-value">
                        <span class="badge badge-priority-${incident.action_priority}">
                            ${getPriorityLabel(incident.action_priority)}
                        </span>
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Incident ID:</span>
                    <span class="detail-value">#${incident.incident_id}</span>
                </div>
            </div>
        </div>

        <div class="modal-section pipeline-flow">
            <h3>🔄 Multi-Agent Pipeline Flow</h3>
            <div class="pipeline-steps">
                <div class="pipeline-step">
                    <div class="step-icon">🔍</div>
                    <div class="step-name">BERT Detection</div>
                    <div class="step-status">✓ Complete</div>
                </div>
                <div class="pipeline-arrow">→</div>
                <div class="pipeline-step">
                    <div class="step-icon">🔗</div>
                    <div class="step-name">Correlation</div>
                    <div class="step-status">✓ Complete</div>
                </div>
                <div class="pipeline-arrow">→</div>
                <div class="pipeline-step">
                    <div class="step-icon">🌐</div>
                    <div class="step-name">TI Enrichment</div>
                    <div class="step-status">✓ Complete</div>
                </div>
                <div class="pipeline-arrow">→</div>
                <div class="pipeline-step">
                    <div class="step-icon">💡</div>
                    <div class="step-name">Response</div>
                    <div class="step-status">✓ Complete</div>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeIncidentModal() {
    const modal = document.getElementById('incident-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('incident-modal');
    if (event.target === modal) {
        closeIncidentModal();
    }
}
