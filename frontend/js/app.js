const API = 'http://127.0.0.1:8003';
let surveyorCy = null;
let hydrologistCy = null;

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tab).classList.add('active');
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        if (tab === 'surveyor') loadSurveyor();
        if (tab === 'hydrologist') loadHydrologist();
    });
});

async function loadOverview() {
    try {
        const res = await fetch(`${API}/api/agents`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const agents = await res.json();
        const s = agents.find(a => a.name === 'Surveyor');
        const h = agents.find(a => a.name === 'Hydrologist');
        if (s) { document.getElementById('s-nodes').textContent = s.nodes; document.getElementById('s-edges').textContent = s.edges; }
        if (h) {
            document.getElementById('h-nodes').textContent = h.nodes;
            document.getElementById('h-edges').textContent = h.edges;
            document.getElementById('h-conf').textContent = `${h.confidence_high} high, ${h.confidence_medium} medium`;
        }
    } catch (err) {
        console.error('Overview error:', err);
    }
}

async function loadSurveyor() {
    console.log('=== Loading Surveyor ===');
    const viz = document.getElementById('surveyor-viz');
    
    try {
        const res = await fetch(`${API}/api/agent/surveyor/graph`);
        
        // Check for non-JSON response
        const contentType = res.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await res.text();
            throw new Error(`Invalid response: ${text.substring(0, 100)}`);
        }
        
        const data = await res.json();
        
        // Check for error in response
        if (data.error) {
            throw new Error(data.error + (data.details ? ': ' + data.details : ''));
        }
        
        console.log('Surveyor data:', data.elements.length, 'elements');
        
        if (!data.elements || data.elements.length === 0) {
            viz.innerHTML = '<p class="empty-state">No module dependencies found</p>';
            return;
        }
        
        if (surveyorCy) surveyorCy.destroy();
        
        surveyorCy = cytoscape({
            container: viz,
            elements: data.elements,
            style: [
                { selector: 'node', style: { 'label': 'data(label)', 'color': '#000', 'text-outline-color': '#fff', 'text-outline-width': 2, 'font-weight': 'bold', 'font-size': '11px', 'width': '50px', 'height': '50px', 'text-valign': 'center', 'text-halign': 'center' } },
                { selector: 'edge', style: { 'width': 2, 'line-color': '#95a5a6', 'target-arrow-color': '#95a5a6', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } },
                { selector: 'node[type="module"]', style: { 'background-color': '#2c3e50' } },
                { selector: 'node[type="yaml"]', style: { 'background-color': '#3498db' } },
                { selector: 'node[type="seed"]', style: { 'background-color': '#27ae60', 'width': '40px', 'height': '40px' } }
            ],
            layout: { name: 'cose', padding: 20, nodeRepulsion: 3000 }
        });
        
        console.log(' Surveyor graph rendered');
        showLegend('surveyor');
        
    } catch (err) {
        console.error('Surveyor error:', err);
        viz.innerHTML = `<p class="error-state">Error: ${err.message}</p>`;
    }
}

async function loadHydrologist() {
    try {
        const res = await fetch(`${API}/api/agent/hydrologist/graph`);
        const data = await res.json();
        if (hydrologistCy) hydrologistCy.destroy();
        hydrologistCy = cytoscape({
            container: document.getElementById('hydrologist-viz'),
            elements: data.elements,
            style: [
                { selector: 'node', style: { 'label': 'data(label)', 'color': '#000', 'text-outline-color': '#fff', 'text-outline-width': 2, 'font-size': '10px', 'width': '45px', 'height': '45px' } },
                { selector: 'edge', style: { 'width': 2, 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } },
                { selector: 'node[type="seed"]', style: { 'background-color': '#27ae60' } },
                { selector: 'node[type="staging"]', style: { 'background-color': '#3498db' } },
                { selector: 'node[type="mart"]', style: { 'background-color': '#f39c12', 'width': '60px', 'height': '60px' } },
                { selector: 'node[type="test"]', style: { 'background-color': '#e74c3c' } }
            ],
            layout: { name: 'cose', padding: 20, nodeRepulsion: 3000 }
        });
        showLegend('hydrologist');
    } catch (err) {
        console.error('Hydrologist error:', err);
    }
}

function showLegend(agent) {
    const container = document.getElementById(`${agent}-legend`);
    if (!container) return;
    const colors = agent === 'surveyor' 
        ? [ {c:'#2c3e50',l:'Module'}, {c:'#3498db',l:'YAML'} ]
        : [ {c:'#27ae60',l:'Seed'}, {c:'#3498db',l:'Staging'}, {c:'#f39c12',l:'Mart'}, {c:'#e74c3c',l:'Test'} ];
    container.innerHTML = `<div class="legend-items">${colors.map(x => `<div class="legend-item"><span class="legend-color" style="background:${x.c}"></span><span>${x.l}</span></div>`).join('')}</div>`;
}

document.addEventListener('DOMContentLoaded', loadOverview);








// Agent 3: Semanticist - Render purpose statements and domain clusters
// ============================================================================
// AGENT 3: SEMANTICIST - CLEAN SINGLE IMPLEMENTATION
// ============================================================================

async function renderSemanticist() {
    console.log('=== Agent 3: Semanticist Loading ===');
    
    const container = document.getElementById('purpose-list-content');
    if (!container) {
        console.error('purpose-statements container not found');
        return;
    }
    
    // Show loading state
    container.innerHTML = '<div style="text-align:center;padding:2rem;color:#3498db">Loading purpose statements...</div>';
    
    try {
        // Use the confirmed working endpoint
        const response = await fetch('/api/agent/semanticist/purposes');
        const data = await response.json();
        
        console.log('Agent 3 API response:', data);
        
        if (!data.ok || !data.purposes) {
            container.innerHTML = '<p style="color:#e74c3c">No data returned from API</p>';
            return;
        }
        
        // Render purpose statements
        let html = '';
        const purposes = data.purposes;
        
        for (const [moduleId, info] of Object.entries(purposes)) {
            const purpose = info.purpose_statement || 'No purpose generated';
            const hasDrift = info.has_drift || info.has_documentation_drift;
            const driftReason = info.drift_reason || 'Documentation contradicts implementation';
            const filePath = info.file_path || '';
            
            // Card styling based on drift status
            const borderColor = hasDrift ? '#ffc107' : '#007bff';
            const bgColor = hasDrift ? '#fffbeb' : '#ffffff';
            
            html += '<div class="card" style="background:' + bgColor + ';border:1px solid #e0e0e0;border-left:4px solid ' + borderColor + ';padding:1rem;margin-bottom:1rem;border-radius:6px">';
            html += '<h4 style="margin:0 0 0.5rem 0;color:#1a1a2e;font-size:1.05rem">' + moduleId + '</h4>';
            html += '<p style="margin:0 0 0.5rem 0;color:#333;line-height:1.5">' + purpose + '</p>';
            
            if (filePath) {
                html += '<small style="color:#6c757d;display:block;margin-bottom:0.5rem">📁 ' + filePath + '</small>';
            }
            
            if (hasDrift) {
                html += '<div style="background:#fff3cd;border-left:3px solid #ffc107;padding:0.5rem 0.75rem;border-radius:4px;margin-top:0.5rem">';
                html += '<strong style="color:#856404;font-size:0.9rem">⚠️ Documentation Drift</strong>';
                html += '<p style="margin:0.25rem 0 0 0;color:#856404;font-size:0.9rem">' + driftReason + '</p>';
                html += '</div>';
            }
            
            html += '</div>';
        }
        
        container.innerHTML = html || '<p style="color:#6c757d">No modules analyzed</p>';
        console.log('✅ Agent 3 rendered successfully -', Object.keys(purposes).length, 'modules');
        
    } catch (error) {
        console.error('❌ Agent 3 error:', error);
        container.innerHTML = '<p style="color:#e74c3c;background:#fdeaea;padding:1rem;border-radius:6px">Error loading Agent 3: ' + error.message + '</p>';
    }
}

// ============================================================================
// AGENT 3: TAB CLICK HANDLER (SINGLE, CLEAN)
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const semBtn = document.querySelector('.tab-btn[data-tab="semanticist"]');
    
    if (semBtn) {
        semBtn.addEventListener('click', function() {
            console.log('Agent 3 tab clicked');
            
            // Deactivate all tabs
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
            
            // Activate semanticist tab
            this.classList.add('active');
            const section = document.getElementById('semanticist');
            if (section) {
                section.classList.add('active');
                section.style.display = 'block';
            }
            
            // Render content after short delay (ensures DOM is ready)
            setTimeout(renderSemanticist, 100);
        });
        
        console.log('✅ Agent 3 tab listener attached');
    }
});


// Ensure proper tab switching - hide all tabs initially
document.addEventListener('DOMContentLoaded', function() {
    // Hide all tab contents on load
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Show only overview by default
    const overview = document.getElementById('overview');
    if (overview) {
        overview.style.display = 'block';
        overview.classList.add('active');
    }
    
    console.log(' Tab system initialized - all tabs hidden except overview');
});

