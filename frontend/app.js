// Multi-Agent SOC Dashboard - JavaScript Logic
// Connects to FastAPI backend running Member 1 + Member 2 agents

const API_BASE = 'http://localhost:8000';

let allIncidents = [];
let lastUploadIncidents = [];  // incidents from the most recent upload only
let currentTab = 'dashboard';
let dashboardMode = 'all'; // 'all' | 'upload'

// Chart instances
let threatChart = null;
let confidenceChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initTabs();
    initFileUpload();
    initFilters();
    loadDashboard();

    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);

    // Restore last-known stats from cache before API responds (per-user key)
    const cacheKey = `soc_incidents_${currentUser}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
        try {
            const cachedIncidents = JSON.parse(cached);
            updateDashboardStats(cachedIncidents);
            updateCharts(cachedIncidents);
            setDashboardBadge('all');
        } catch (e) { /* ignore corrupt cache */ }
    } else {
        // New user — render null/empty state explicitly
        renderNullState();
    }

    document.getElementById('refresh-btn').addEventListener('click', () => {
        dashboardMode = 'all';
        lastUploadIncidents = [];
        loadDashboard();
        showNotification('Showing all-time incidents', 'info');
    });
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

// Load dashboard data (all-time)
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/incidents?limit=1000`);
        if (!response.ok) throw new Error('Backend not available');

        allIncidents = await response.json();
        console.log('📊 Loaded incidents:', allIncidents.length);

        // Cache to localStorage per-user for instant-load on next page visit
        const cacheKey = `soc_incidents_${currentUser}`;
        localStorage.setItem(cacheKey, JSON.stringify(allIncidents));

        // Only update charts if we are NOT in per-upload mode
        if (dashboardMode === 'all') {
            updateDashboardStats(allIncidents);
            updateCharts(allIncidents);
            setDashboardBadge('all');
        }

        if (currentTab === 'incidents') {
            displayIncidents(allIncidents);
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showNotification('Backend not available. Please start the FastAPI server.', 'error');
    }
}

// Render null / empty state for new users with no history
function renderNullState() {
    ['total-incidents', 'high-severity', 'avg-confidence', 'critical-actions'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '—';
    });
}

// Update dashboard statistics
function updateDashboardStats(incidents) {
    console.log('📈 Updating stats for', incidents.length, 'incidents');

    if (!incidents || incidents.length === 0) {
        renderNullState();
        return;
    }

    const total = incidents.length;
    const highSeverity = incidents.filter(i => i.severity === 'HIGH').length;
    const mediumSeverity = incidents.filter(i => i.severity === 'MEDIUM').length;
    const lowSeverity = incidents.filter(i => i.severity === 'LOW').length;
    const criticalActions = incidents.filter(i => i.action_priority === 1).length;

    const avgConfidence = (incidents.reduce((sum, i) => sum + (i.avg_confidence || i.bert_confidence || 0), 0) / incidents.length * 100).toFixed(1);

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

function displayIncidents(incidents, groupBy = '') {
    const tbody = document.getElementById('incidents-body');
    const thead = document.querySelector('#incidents-table thead tr');
    tbody.innerHTML = '';

    if (incidents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="no-data">No incidents to display. Upload logs to analyze.</td></tr>';
        return;
    }

    // --- GROUPED MODE ---
    if (groupBy) {
        // Hide table header — we render group headers instead
        thead.style.display = 'none';

        // Build group key extractor
        const getKey = (inc) => {
            switch (groupBy) {
                case 'ip': return getSourceIp(inc) || 'Unknown';
                case 'threat': return (inc.threat_type || inc.bert_class || 'Unknown').replace('_', ' ').toUpperCase();
                case 'severity': return inc.severity || 'Unknown';
                case 'priority': return getPriorityLabel(inc.action_priority);
                default: return 'All';
            }
        };

        // Group incidents
        const groups = {};
        incidents.forEach(inc => {
            const key = getKey(inc);
            if (!groups[key]) groups[key] = [];
            groups[key].push(inc);
        });

        // Sort groups by count descending
        const sortedKeys = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);

        sortedKeys.forEach(key => {
            const groupIncidents = groups[key];

            // Group header row
            const headerRow = document.createElement('tr');
            headerRow.className = 'group-header-row';
            headerRow.innerHTML = `
                <td colspan="10">
                    <div class="group-header-inner">
                        <span class="group-toggle" onclick="toggleGroup(this)">▾</span>
                        <span class="group-label">${key}</span>
                        <span class="group-count">${groupIncidents.length} incident${groupIncidents.length !== 1 ? 's' : ''}</span>
                    </div>
                </td>
            `;
            tbody.appendChild(headerRow);

            // Incident rows for this group
            groupIncidents.forEach((incident, index) => {
                const row = buildIncidentRow(incident, incidents.indexOf(incident));
                row.className = 'group-member-row';
                tbody.appendChild(row);
            });
        });

        // --- FLAT MODE ---
    } else {
        thead.style.display = '';
        incidents.forEach((incident, index) => {
            tbody.appendChild(buildIncidentRow(incident, index));
        });
    }
}

function toggleGroup(btn) {
    const headerRow = btn.closest('tr');
    let next = headerRow.nextElementSibling;
    let hidden = false;
    while (next && next.classList.contains('group-member-row')) {
        if (!hidden) hidden = next.style.display === 'none';
        next.style.display = next.style.display === 'none' ? '' : 'none';
        next = next.nextElementSibling;
    }
    btn.textContent = hidden ? '▾' : '▸';
}

function buildIncidentRow(incident, index) {
    const sourceIp = getSourceIp(incident);
    const alertCount = getAlertCount(incident);
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><code>${sourceIp}</code></td>
        <td><span class="badge badge-threat">${(incident.threat_type || '').replace('_', ' ').toUpperCase()}</span></td>
        <td><span class="badge badge-${incident.severity.toLowerCase()}">${incident.severity}</span></td>
        <td><span class="badge badge-count">${alertCount}</span></td>
        <td><span class="badge badge-confidence">${(incident.avg_confidence * 100).toFixed(1)}%</span></td>
        <td><small>${incident.enrichment?.location || 'N/A'}</small></td>
        <td><span class="badge badge-action">${incident.recommended_action}</span></td>
        <td><span class="badge badge-priority-${incident.action_priority}">${getPriorityLabel(incident.action_priority)}</span></td>
        <td><small>${formatTimestamp(incident.timestamp)}</small></td>
        <td><button class="btn-details" onclick="showIncidentDetails(${index})">🔍 View</button></td>
    `;
    return row;
}

function getPriorityLabel(priority) {
    const labels = { 1: 'Critical', 2: 'High', 3: 'Medium' };
    return labels[priority] || 'Low';
}

function getSourceIp(incident) {
    return incident?.source_ip || incident?.ip || incident?.src_ip || incident?.sourceIp || incident?.attacker_ip || 'N/A';
}

function getAlertCount(incident) {
    return incident?.alert_count ?? incident?.alerts_count ?? incident?.alerts ?? incident?.correlated_events ?? 0;
}

function getTiCategory(incident) {
    return incident?.ti_category || incident?.enrichment?.ti_category || incident?.enrichment?.category || incident?.threat_type || 'N/A';
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Auth session
let currentUser = null;

function initAuth() {
    const sessionStr = localStorage.getItem('soc_session');
    if (!sessionStr) {
        window.location.replace('auth.html');
        return;
    }
    try {
        const session = JSON.parse(sessionStr);
        currentUser = session.username || 'user';
        const nameEl = document.getElementById('user-name');
        if (nameEl) nameEl.textContent = currentUser;
    } catch (e) {
        localStorage.removeItem('soc_session');
        window.location.replace('auth.html');
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            // Clear this user's incident cache on logout
            if (currentUser) {
                localStorage.removeItem(`soc_incidents_${currentUser}`);
            }
            localStorage.removeItem('soc_session');
            window.location.replace('auth.html');
        });
    }
}

// Filters
function initFilters() {
    const severityFilter = document.getElementById('severity-filter');
    const searchInput = document.getElementById('search-input');
    const groupBySelect = document.getElementById('group-by-select');

    severityFilter.addEventListener('change', applyFilters);
    searchInput.addEventListener('input', applyFilters);
    groupBySelect.addEventListener('change', applyFilters);
}

function applyFilters() {
    const severity = document.getElementById('severity-filter').value;
    const search = document.getElementById('search-input').value.toLowerCase();
    const groupBy = document.getElementById('group-by-select').value;

    let filtered = allIncidents;

    if (severity) {
        filtered = filtered.filter(i => i.severity === severity);
    }

    if (search) {
        filtered = filtered.filter(i =>
            getSourceIp(i).toLowerCase().includes(search) ||
            (i.threat_type || '').toLowerCase().includes(search)
        );
    }

    displayIncidents(filtered, groupBy);
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
                <p>Incidents detected: <strong>${result.incidents_detected ?? result.incidents_count ?? 0}</strong></p>
                <p>Pipeline: BERT Detection → Correlation → TI Enrichment → Response Recommendations</p>
                <button class="btn-primary" onclick="switchTab('incidents')">View Incidents</button>
            `;

            // Use returned incidents for per-upload dashboard view
            if (result.incidents && result.incidents.length > 0) {
                lastUploadIncidents = result.incidents;
                dashboardMode = 'upload';
                updateDashboardStats(lastUploadIncidents);
                updateCharts(lastUploadIncidents);
                setDashboardBadge('upload', file.name);
                showNotification(`Dashboard shows ${file.name} — hit 🔄 for all-time view.`, 'success');
            } else {
                dashboardMode = 'all';
                loadDashboard();
                showNotification('No threats detected in uploaded file.', 'info');
            }

            // Reset upload form
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

// Dashboard mode badge
function setDashboardBadge(mode, filename = '') {
    const badge = document.getElementById('dashboard-badge');
    if (!badge) return;
    if (mode === 'upload') {
        badge.style.display = 'flex';
        badge.className = 'dashboard-badge badge-upload-mode';
        badge.innerHTML = `
            <span class="badge-icon">📄</span>
            <span>Showing results for: <strong>${filename}</strong></span>
            <span class="badge-hint">Hit 🔄 to view all-time data</span>
        `;
    } else {
        badge.style.display = 'flex';
        badge.className = 'dashboard-badge badge-all-mode';
        badge.innerHTML = `
            <span class="badge-icon">🗄️</span>
            <span>Showing <strong>all-time</strong> incidents from database</span>
        `;
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
    const alertCount = getAlertCount(incident);
    const tiCategory = getTiCategory(incident);

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
                    <span class="detail-value"><code>${getSourceIp(incident)}</code></span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Alert Count:</span>
                    <span class="detail-value"><strong>${alertCount}</strong> correlated events</span>
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
                    <span class="detail-label">TI Category:</span>
                    <span class="detail-value">${tiCategory}</span>
                </div>
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
window.onclick = function (event) {
    const modal = document.getElementById('incident-modal');
    if (event.target === modal) {
        closeIncidentModal();
    }
}
