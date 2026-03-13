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
async function renderSemanticist() {
    console.log('Loading Semanticist...');
    try {
        const [purposesRes, domainsRes] = await Promise.all([
            fetch('/api/agent/semanticist/purposes'),
            fetch('/api/agent/semanticist/domains')
        ]);
        const purposes = await purposesRes.json();
        const domains = await domainsRes.json();
        
        console.log('Semanticist data:', purposes, domains);
        
        // Display purpose statements
        const listDiv = document.getElementById('purpose-list-content');
        if (listDiv && purposes.purposes) {
            let html = '';
            for (const [id, data] of Object.entries(purposes.purposes)) {
                const purpose = data.purpose_statement || 'No purpose statement';
                const file = data.file_path || '';
                html += '<div style="background:#f8f9fa;padding:1rem;border-radius:8px;border-left:3px solid #3498db;margin-bottom:1rem">';
                html += '<strong style="color:#2c3e50">' + id + '</strong>';
                html += '<p style="margin:0.5rem 0 0 0;color:#555;font-size:0.9rem">' + purpose + '</p>';
                if (file) {
                    html += '<div style="margin-top:0.5rem;font-size:0.8rem;color:#7f8c8d"> ' + file + '</div>';
                }
                html += '</div>';
            }
            listDiv.innerHTML = html;
        }
        
        // Display domain clusters
        const vizDiv = document.getElementById('semanticist-viz');
        if (vizDiv && domains.clusters) {
            let clusterHTML = '';
            for (const [domain, modules] of Object.entries(domains.clusters)) {
                if (typeof domain === 'string' && !['purpose_statement','has_documentation_drift','drift_reason'].includes(domain)) {
                    clusterHTML += '<div style="margin:1rem 0;padding:1rem;background:#f8f9fa;border-radius:8px;border-left:3px solid #27ae60">';
                    clusterHTML += '<h4 style="margin:0 0 0.5rem 0;color:#2c3e50"> ' + domain + '</h4>';
                    clusterHTML += '<div style="display:flex;flex-wrap:wrap;gap:0.5rem">';
                    for (const m of modules) {
                        clusterHTML += '<span style="background:#3498db;color:white;padding:0.25rem 0.5rem;border-radius:4px;font-size:0.85rem">' + m + '</span>';
                    }
                    clusterHTML += '</div></div>';
                }
            }
            vizDiv.innerHTML = '<div style="padding:1rem">' + clusterHTML + '</div>';
        }
        
        console.log(' Semanticist rendered');
    } catch (e) {
        console.error(' Semanticist error:', e);
    }
}


// Agent 3 tab click listener
document.addEventListener('DOMContentLoaded', function() {
    const semBtn = document.querySelector('.tab-btn[data-tab="semanticist"]');
    if (semBtn) {
        semBtn.addEventListener('click', function() {
            console.log('Agent 3 tab clicked');
            setTimeout(function() {
                if (typeof renderSemanticist === 'function') {
                    renderSemanticist();
                }
            }, 100);
        });
    }
});

// Agent 3: Semanticist - Simple render function
async function renderSemanticist() {
    console.log('=== SEMANTICIST RENDER START ===');
    try {
        const purposesRes = await fetch('/api/agent/semanticist/purposes');
        const purposesData = await purposesRes.json();
        console.log('API Response:', purposesData);
        
        const purposes = purposesData.purposes || {};
        console.log('Purposes count:', Object.keys(purposes).length);
        console.log('Purposes keys:', Object.keys(purposes));
        
        const listDiv = document.getElementById('purpose-list-content');
        console.log('listDiv exists:', listDiv !== null);
        
        if (listDiv && Object.keys(purposes).length > 0) {
            let html = '<h4 style="margin-bottom:1rem;color:#2c3e50">Purpose Statements</h4>';
            for (const [id, data] of Object.entries(purposes)) {
                const purpose = data.purpose_statement || 'No statement';
                const file = data.file_path || '';
                html += '<div style="background:#fff;border:1px solid #e0e0e0;padding:1rem;border-radius:8px;margin-bottom:1rem">';
                html += '<strong>' + id + '</strong><br>';
                html += '<small style="color:#555">' + purpose + '</small>';
                if (file) html += '<br><small style="color:#7f8c8d"> ' + file + '</small>';
                html += '</div>';
            }
            listDiv.innerHTML = html;
            console.log(' Purpose statements rendered');
        } else if (listDiv) {
            listDiv.innerHTML = '<p>No purposes data</p>';
            console.log(' No purposes to render');
        }
        
        console.log('=== SEMANTICIST RENDER END ===');
    } catch (e) {
        console.error(' Error:', e);
    }
}

// Tab listener
document.addEventListener('DOMContentLoaded', function() {
    const semBtn = document.querySelector('.tab-btn[data-tab="semanticist"]');
    if (semBtn) {
        semBtn.addEventListener('click', function() {
            console.log('Tab clicked, calling renderSemanticist');
            setTimeout(renderSemanticist, 100);
        });
    }
});





// Ensure semanticist tab activates properly
document.addEventListener('DOMContentLoaded', function() {
    const semBtn = document.querySelector('.tab-btn[data-tab="semanticist"]');
    const semSection = document.getElementById('semanticist');
    
    if (semBtn && semSection) {
        semBtn.addEventListener('click', function() {
            // Remove active from all tabs
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(s => {
                s.classList.remove('active');
                s.style.display = 'none';
            });
            
            // Activate semanticist
            semBtn.classList.add('active');
            semSection.classList.add('active');
            semSection.style.display = 'block';
            
            // Render content after a short delay
            setTimeout(function() {
                if (typeof renderSemanticist === 'function') {
                    renderSemanticist();
                }
            }, 50);
        });
    }
});






// ============================================================================
// AGENT 3: SEMANTICIST - Clean Render Function
// ============================================================================

async function renderSemanticist() {
    console.log('=== SEMANTICIST RENDER (CLEAN) ===');
    
    const vizDiv = document.getElementById('semanticist-viz');
    if (!vizDiv) {
        console.error(' semanticist-viz not found');
        return;
    }
    
    // Show loading
    vizDiv.innerHTML = '<div style="padding:2rem;text-align:center;color:#3498db;font-size:1.2rem"> Loading...</div>';
    
    try {
        const [pRes, dRes] = await Promise.all([
            fetch('/api/agent/semanticist/purposes'),
            fetch('/api/agent/semanticist/domains')
        ]);
        
        const pData = await pRes.json();
        const dData = await dRes.json();
        
        console.log(' Purposes:', pData);
        console.log(' Domains:', dData);
        
        // Build HTML
        let html = '<div style="padding:1.5rem;font-family:system-ui,sans-serif">';
        
        // PURPOSES SECTION
        html += '<div style="margin-bottom:2rem">';
        html += '<h3 style="color:#1a1a2e;margin-bottom:1rem;font-size:1.3rem;border-bottom:3px solid #3498db;padding-bottom:0.5rem"> Purpose Statements</h3>';
        
        if (pData.purposes && Object.keys(pData.purposes).length > 0) {
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:1rem">';
            
            for (const [id, data] of Object.entries(pData.purposes)) {
                // Handle different data structures
                const purpose = data?.purpose_statement || data?.purpose || String(data);
                const file = data?.file_path || data?.file || '';
                
                html += '<div style="background:#fff;border:1px solid #e0e0e0;border-left:4px solid #3498db;padding:1.2rem;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.08)">';
                html += '<div style="font-weight:700;color:#1a1a2e;margin-bottom:0.75rem;font-size:1.05rem">'+id+'</div>';
                html += '<div style="color:#333;line-height:1.6;font-size:0.95rem">'+purpose+'</div>';
                if (file) {
                    html += '<div style="margin-top:0.75rem;padding:0.4rem 0.6rem;background:#f5f5f5;border-radius:4px;font-size:0.85rem;color:#666"> '+file+'</div>';
                }
                html += '</div>';
            }
            html += '</div>';
        } else {
            html += '<p style="color:#7f8c8d;padding:1rem;background:#f8f9fa;border-radius:6px">No purpose statements available</p>';
        }
        
        html += '</div>';
        
        // DOMAINS SECTION
        html += '<div>';
        html += '<h3 style="color:#1a1a2e;margin-bottom:1rem;font-size:1.3rem;border-bottom:3px solid #27ae60;padding-bottom:0.5rem"> Domain Clusters</h3>';
        
        if (dData.clusters && Object.keys(dData.clusters).length > 0) {
            for (const [domain, modules] of Object.entries(dData.clusters)) {
                if (typeof domain === 'string' && domain.length > 2 && !domain.includes('purpose') && !domain.includes('drift')) {
                    html += '<div style="margin:1rem 0;padding:1.2rem;background:#f8f9fa;border-radius:8px;border-left:4px solid #27ae60">';
                    html += '<div style="font-weight:700;color:#1a1a2e;margin-bottom:0.75rem;font-size:1.1rem;text-transform:capitalize">'+domain.replace(/_/g,' ')+'</div>';
                    html += '<div style="display:flex;flex-wrap:wrap;gap:0.5rem">';
                    if (Array.isArray(modules)) {
                        for (const m of modules) {
                            html += '<span style="background:#3498db;color:#fff;padding:0.35rem 0.7rem;border-radius:4px;font-size:0.85rem;font-weight:500">'+m+'</span>';
                        }
                    }
                    html += '</div></div>';
                }
            }
        } else {
            html += '<p style="color:#7f8c8d;padding:1rem;background:#f8f9fa;border-radius:6px">No domain clusters</p>';
        }
        
        html += '</div></div>';
        
        vizDiv.innerHTML = html;
        console.log(' Rendered successfully - HTML length:', html.length);
        
    } catch (e) {
        vizDiv.innerHTML = '<div style="padding:2rem;color:#e74c3c;background:#fdeaea;border-radius:8px"><strong> Error:</strong> '+e.message+'</div>';
        console.error(' Error:', e);
    }
}

// Tab click handler (only once)
document.addEventListener('DOMContentLoaded', function() {
    const semBtn = document.querySelector('.tab-btn[data-tab="semanticist"]');
    if (semBtn) {
        semBtn.addEventListener('click', function() {
            console.log(' Agent 3 tab clicked');
            
            // Deactivate all tabs
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(s => {
                s.classList.remove('active');
                s.style.display = 'none';
            });
            
            // Activate semanticist
            this.classList.add('active');
            const section = document.getElementById('semanticist');
            if (section) {
                section.classList.add('active');
                section.style.display = 'block';
            }
            
            // Render after short delay
            setTimeout(renderSemanticist, 50);
        });
        
        console.log(' Semanticist tab listener attached');
    }
});
