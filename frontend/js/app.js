/**
 * EMERALD AUDITOR / BROWNFIELD CARTOGRAPHER
 * Core Application Logic - Integrated Build
 */

const CONFIG = {
    API_BASE: 'http://127.0.0.1:8003',
    COLORS: {
        module: '#1a1a2e',
        yaml: '#3498db',
        seed: '#27ae60',
        staging: '#2980b9',
        mart: '#f39c12',
        test: '#e74c3c'
    }
};

let state = {
    currentRepo: localStorage.getItem('current_repo') || '',
    graphs: { surveyor: null, hydrologist: null }
};

// ============================================================================
// 1. INITIALIZATION & ROUTING
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initAnalysisTrigger();
    
    // Auto-load if repo exists in state
    if (state.currentRepo) {
        console.log(`Resuming session: ${state.currentRepo}`);
    }
});

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // UI Toggle
            document.querySelectorAll('.tab-btn, .tab-content').forEach(el => el.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');

            // Load logic based on tab
            if (!state.currentRepo && tabId !== 'overview' && tabId !== 'methodology') {
                alert("Please run a Swarm Analysis on the Overview tab first.");
                return;
            }

            switch(tabId) {
                case 'surveyor': loadGraphAgent('surveyor'); break;
                case 'hydrologist': loadGraphAgent('hydrologist'); break;
                case 'semanticist': renderSemantics(); break;
                case 'archivist': loadArchivist(); break;
            }
        });
    });
}

// ============================================================================
// 2. THE SWARM COMMANDER (Timing & Execution)
// ============================================================================
function initAnalysisTrigger() {
    const btn = document.getElementById('analyze-btn');
    const input = document.getElementById('repo-url-input');
    const logs = document.getElementById('analysis-logs');

    if (!btn) return;

    btn.addEventListener('click', async () => {
        const repoUrl = input.value.trim();
        if (!repoUrl) return;

        const startTime = performance.now(); // Start Timer
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        logs.innerHTML = `> [${new Date().toLocaleTimeString()}] SWARM INITIATED: Targeting ${repoUrl}`;

        try {
            const response = await fetch(`${CONFIG.API_BASE}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: repoUrl })
            });
            const result = await response.json();

            const duration = ((performance.now() - startTime) / 1000).toFixed(2); // Stop Timer
            
            // Update Global State
            state.currentRepo = result.local_path;
            localStorage.setItem('current_repo', result.local_path);
            
            // Update Dashboard Stats
            document.getElementById('stat-duration').textContent = `${duration}s`;
            document.getElementById('stat-nodes').textContent = result.stats?.total_nodes || 0;
            document.getElementById('stat-edges').textContent = result.stats?.total_edges || 0;
            document.getElementById('stat-drift').textContent = result.stats?.drift_count || 0;

            logs.innerHTML += `\n> [${new Date().toLocaleTimeString()}] SUCCESS: Forensic trace complete.`;
            logs.innerHTML += `\n> AUDIT DURATION: ${duration} seconds.`;
            logs.scrollTop = logs.scrollHeight;

        } catch (err) {
            logs.innerHTML += `\n> [ERROR] Analysis failed: ${err.message}`;
        } finally {
            btn.disabled = false;
            btn.innerText = 'Run Swarm Analysis';
        }
    });
}

// ============================================================================
// 3. GRAPH VISUALIZATION ENGINE (Surveyor & Hydrologist)
// ============================================================================
async function loadGraphAgent(agentType) {
    const container = document.getElementById(`${agentType}-viz`);
    const inspector = document.getElementById(`${agentType}-inspector`);
    
    if (!container) return;

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/agent/${agentType}/graph?repo_path=${encodeURIComponent(state.currentRepo)}`);
        const data = await res.json();

        // Cleanup existing graph to prevent memory leaks
        if (state.graphs[agentType]) state.graphs[agentType].destroy();

        state.graphs[agentType] = cytoscape({
            container: container,
            elements: data.elements,
            style: [
                { selector: 'node', style: { 
                    'label': 'data(label)', 'color': '#333', 'font-size': '10px',
                    'text-valign': 'center', 'text-halign': 'center',
                    'background-color': (n) => CONFIG.COLORS[n.data('type')] || '#ccc',
                    'width': 40, 'height': 40, 'text-outline-width': 2, 'text-outline-color': '#fff'
                }},
                { selector: 'edge', style: { 
                    'width': 2, 'line-color': '#ddd', 'target-arrow-color': '#ddd', 
                    'target-arrow-shape': 'triangle', 'curve-style': 'bezier' 
                }}
            ],
            layout: { name: 'cose', padding: 30, animate: true }
        });

        // HANDLE CLICK -> POPULATE RIGHT SIDE INSPECTOR
        state.graphs[agentType].on('tap', 'node', (evt) => {
            const node = evt.target.data();
            inspector.style.display = 'block';
            inspector.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ddd; padding-bottom:10px; margin-bottom:15px;">
                    <h4 style="margin:0; font-family:sans-serif;">Node Details</h4>
                    <button onclick="this.parentElement.parentElement.style.display='none'" style="border:none; background:none; cursor:pointer; font-size:1.5rem; line-height:1;">&times;</button>
                </div>
                <div style="font-size: 0.85rem; font-family: sans-serif; line-height:1.6;">
                    <p><strong>ID:</strong> <code style="word-break:break-all; background:#eee; padding:2px 4px; border-radius:3px;">${node.id}</code></p>
                    <p><strong>Type:</strong> <span style="background:${CONFIG.COLORS[node.type] || '#888'}; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem;">${node.type}</span></p>
                    ${node.file_path ? `<p><strong>Source Trace:</strong><br><small style="color:#2980b9; display:block; margin-top:4px;">${node.file_path}</small></p>` : ''}
                </div>
                <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
                <div style="background:#f4f7f9; padding:12px; border-radius:6px; font-size:0.75rem; color:#555; border:1px solid #e1e8ed;">
                    <i class="fas fa-shield-alt" style="color:#27ae60;"></i> Forensic Anchor Verified
                </div>
            `;
        });

    } catch (e) { 
        console.error(`Failed to load ${agentType}`, e);
        container.innerHTML = `<div style="padding:20px; color:red;">Error loading graph agent. Ensure the backend is running at ${CONFIG.API_BASE}</div>`;
    }
}

// ============================================================================
// 4. SEMANTICS & ARTIFACTS (Semanticist & Archivist)
// ============================================================================
async function renderSemantics() {
    const container = document.getElementById('purpose-list-content');
    if (!container) return;
    
    container.innerHTML = '<div style="padding:2rem;">Loading semantic models...</div>';
    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/agent/semanticist/full?repo_path=${encodeURIComponent(state.currentRepo)}`);
        const data = await res.json();
        const purposes = data.purposes || data.result?.purpose_statements || {};

        if (Object.keys(purposes).length === 0) {
            container.innerHTML = '<div style="padding:2rem;">No semantic data available.</div>';
            return;
        }

        container.innerHTML = Object.entries(purposes).map(([id, info]) => `
            <div style="background:white; padding:1.5rem; border-radius:8px; border-left:4px solid ${info.has_drift ? CONFIG.COLORS.test : CONFIG.COLORS.seed}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h4 style="margin:0 0 10px 0; font-family:sans-serif;">${id}</h4>
                <p style="font-size:0.9rem; line-height:1.4; color:#555; font-family:sans-serif;">${info.purpose_statement || 'No description extracted.'}</p>
                ${info.has_drift ? `
                    <div style="margin-top:10px; padding:8px; background:#fff5f5; border-radius:4px; border:1px solid #feb2b2;">
                        <small style="color:#c53030; font-weight:600;">⚠️ Documentation Drift: ${info.drift_reason || 'Inconsistent implementation.'}</small>
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (e) { 
        container.innerHTML = '<div style="padding:2rem; color:red;">Error loading semantics.</div>'; 
    }
}

async function loadArchivist() {
    const container = document.getElementById('archivist-artifacts');
    if (!container) return;

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/agent/archivist/artifacts?repo_path=${encodeURIComponent(state.currentRepo)}`);
        const data = await res.json();
        const art = data.artifacts || {};

        if (Object.keys(art).length === 0) {
            container.innerHTML = '<div style="padding:2rem;">No living artifacts found.</div>';
            return;
        }

        container.innerHTML = Object.entries(art).map(([name, path]) => `
            <div style="background:white; padding:1.25rem; border-radius:8px; border:1px solid #eee; display:flex; justify-content:space-between; align-items:center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-family:sans-serif;">
                    <i class="fas fa-file-code" style="color:#3498db; margin-right:10px;"></i>
                    <strong style="font-size:0.9rem;">${name.replace(/_/g, ' ').toUpperCase()}</strong>
                </div>
                <button onclick="window.open('${CONFIG.API_BASE}/api/file?path=${encodeURIComponent(path)}')" 
                        style="background:#f8f9fa; border:1px solid #ddd; padding:6px 15px; border-radius:4px; cursor:pointer; font-size:0.8rem; font-weight:600; color:#444;">
                    View Artifact
                </button>
            </div>
        `).join('');
    } catch (e) { 
        container.innerHTML = '<div style="padding:2rem; color:red;">No artifacts found.</div>'; 
    }
}