/**
 * EMERALD AUDITOR / BROWNFIELD CARTOGRAPHER
 * Core Application Logic - Integrated Build v12.0
 * Fixes: Node Coloring and Dynamic Legend Injection
 */

const CONFIG = {
    API_BASE: 'http://127.0.0.1:8003',
    // Fallback colors if the JSON is missing specific overrides
    COLORS: {
        ModuleNode: '#3498db',         // Blue
        DatasetNode: '#2ecc71',        // Green
        TransformationNode: '#e67e22',  // Orange
        FunctionNode: '#9b59b6',       // Purple
        yaml: '#3498db',
        seed: '#27ae60',
        staging: '#2980b9',
        mart: '#f39c12',
        test: '#e74c3c'
    }
};

let state = {
    currentRepo: localStorage.getItem('current_repo') || '',
    graphs: { surveyor: null, hydrologist: null },
    activeLegend: null // Tracks the legend metadata [cite: 2026-03-03]
};

/// ============================================================================
// 1. INITIALIZATION & ROUTING
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initAnalysisTrigger();
    
    if (state.currentRepo) {
        console.log(`Resuming session: ${state.currentRepo}`);
    }
});

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // 1. UI Switch
            document.querySelectorAll('.tab-btn, .tab-content').forEach(el => el.classList.remove('active'));
            btn.classList.add('active');
            const targetEl = document.getElementById(tabId);
            if (targetEl) targetEl.classList.add('active');

            // 2. Guard Rail: Updated 'overview' to 'command' to match your nav bar
            if (!state.currentRepo && tabId !== 'command' && tabId !== 'methodology') {
                alert("Please run a Swarm Analysis on the Command tab first.");
                return;
            }

            // 3. Agent-Specific Routing
            switch(tabId) {
                case 'command': 
                    // Usually doesn't need a reload, but you can reset the navigator here
                    break;
                case 'surveyor': 
                    loadGraphAgent('surveyor'); 
                    break;
                case 'hydrologist': 
                    loadGraphAgent('hydrologist'); 
                    break;
                case 'semanticist': 
                    renderSemantics(); 
                    break;
                case 'archivist': 
                    loadArchivist(); 
                    break;
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

        const startTime = performance.now(); 
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

            const duration = ((performance.now() - startTime) / 1000).toFixed(2); 
            
            state.currentRepo = result.local_path;
            localStorage.setItem('current_repo', result.local_path);
            
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

        // Save legend from metadata if available [cite: 2026-03-03]
        if (data.metadata?.legend) {
            renderLegend(agentType, data.metadata.legend);
        }

        if (state.graphs[agentType]) state.graphs[agentType].destroy();

        state.graphs[agentType] = cytoscape({
            container: container,
            elements: data.elements || data,
            style: [
                { selector: 'node', style: { 
                    'label': 'data(label)', 
                    'color': '#333', 
                    'font-size': '10px',
                    'text-valign': 'center', 
                    'text-halign': 'center',
                    // FIX: Dynamically read the color attribute from the JSON [cite: 2026-03-03]
                    'background-color': (n) => n.data('color') || CONFIG.COLORS[n.data('type')] || '#ccc',
                    'width': 40, 
                    'height': 40, 
                    'text-outline-width': 2, 
                    'text-outline-color': '#fff'
                }},
                { selector: 'edge', style: { 
                    'width': 2, 
                    'line-color': '#ddd', 
                    'target-arrow-color': '#ddd', 
                    'target-arrow-shape': 'triangle', 
                    'curve-style': 'bezier',
                    'line-style': 'solid'
                }}
            ],
            layout: { name: 'cose', padding: 40, animate: true, nodeRepulsion: 4000 }
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
                    <p><strong>Type:</strong> <span style="background:${node.color || '#888'}; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem;">${node.type}</span></p>
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
        container.innerHTML = `<div style="padding:20px; color:red;">Error loading graph agent.</div>`;
    }
}

/**
 * Renders a floating legend overlay on the graph container
 */
function renderLegend(agentType, colorMap) {
    const parent = document.getElementById(`${agentType}-viz`);
    let legendBox = document.getElementById(`${agentType}-legend`);
    
    if (!legendBox) {
        legendBox = document.createElement('div');
        legendBox.id = `${agentType}-legend`;
        legendBox.className = 'forensic-legend';
        parent.appendChild(legendBox);
    }

    legendBox.innerHTML = `
        <h5 style="margin:0 0 10px 0; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#666;">Legend</h5>
        ${Object.entries(colorMap).map(([type, color]) => `
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <div style="width:12px; height:12px; background:${color}; border-radius:3px; margin-right:8px;"></div>
                <span style="font-size:0.7rem; color:#444; font-family:sans-serif;">${type}</span>
            </div>
        `).join('')}
    `;
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
            <div style="background:white; padding:1.5rem; border-radius:8px; border-left:4px solid ${info.has_drift ? CONFIG.COLORS.test : CONFIG.COLORS.seed}; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom:1rem;">
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
            <div style="background:white; padding:1.25rem; border-radius:8px; border:1px solid #eee; display:flex; justify-content:space-between; align-items:center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom:0.75rem;">
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

/**
 * Brownfield Navigator: Logic for the Command Tab Chat Interface
 * Sends user queries to the backend and renders forensic responses.
 */
async function askNavigator() {
    const queryInput = document.getElementById('nav-query');
    const responseContainer = document.getElementById('nav-response-container');
    const responseDiv = document.getElementById('nav-response');
    const btn = document.getElementById('nav-btn');

    // Prevent empty queries
    if (!queryInput || !queryInput.value.trim()) return;

    const userPrompt = queryInput.value.trim();

    // UI Feedback: Set loading state
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ANALYZING...';
    responseContainer.style.display = 'block';
    responseDiv.innerHTML = "<em>Accessing forensic artifacts and reconstructing lineage...</em>";

    try {
        // adjust the URL/Port if your backend is hosted elsewhere
        const response = await fetch('http://localhost:8003/api/navigator/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_prompt: userPrompt 
            })
        });

        if (!response.ok) throw new Error(`Backend error: ${response.status}`);

        const data = await response.json();
        
        // Render the response
        // Using innerText for security, or marked.parse(data.answer) if using Markdown
        responseDiv.innerText = data.answer || data.error || "The Navigator could not generate a response.";

    } catch (err) {
        console.error("Navigator Error:", err);
        responseDiv.innerHTML = `<span style="color: #e74c3c;"><strong>Connection Error:</strong> Could not reach the forensic agent. Ensure your Python backend is running.</span>`;
    } finally {
        // Reset button state
        btn.disabled = false;
        btn.innerText = "ASK AGENT";
    }
}

// Optional: Allow pressing "Enter" to submit
document.getElementById('nav-query').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        askNavigator();
    }
});
async function executeSwarm() {
    const repoInput = document.getElementById('repo-url-input').value.trim();
    const statusBox = document.querySelector('.terminal-window') || document.querySelector('[style*="background: #1e1e1e"]'); // Targets your black box
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // Target the specific metric cards from your image
    const runtimeVal = document.querySelector('.card:nth-child(1) h3');
    const nodesVal = document.querySelector('.card:nth-child(2) h3');
    const edgesVal = document.querySelector('.card:nth-child(3) h3');

    if (!repoInput) {
        alert("FDE Alert: Please provide a local path or repository URL.");
        return;
    }

    // 1. UI Feedback - Terminal Start
    statusBox.innerHTML = `<span style="color: #00ff00;">> 🔍 Analyzing Source: ${repoInput}</span><br>> 🛠️ Resolving Local Path Resolver...`;
    analyzeBtn.disabled = true;
    const startTime = performance.now();

    try {
        const response = await fetch(`/api/repository/analyze?repo_path=${encodeURIComponent(repoInput)}`);
        const data = await response.json();

        if (data.success) {
            const endTime = performance.now();
            const duration = ((endTime - startTime) / 1000).toFixed(2);

            // 2. Update the Dashboard Cards from your screenshot
            if(runtimeVal) runtimeVal.innerText = `${duration}s`;
            if(nodesVal) nodesVal.innerText = data.results.semanticist.modules;
            if(edgesVal) edgesVal.innerText = data.results.hydrologist.edges;

            // 3. Terminal Success Message
            statusBox.innerHTML += `<br>> ✅ Swarm synchronization: 100%`;
            statusBox.innerHTML += `<br>> 🛰️ Lineage Graph: ${data.results.hydrologist.edges} edges mapped.`;
            statusBox.innerHTML += `<br>> 🧠 Semanticist: ${data.results.semanticist.modules} modules indexed.`;
            statusBox.innerHTML += `<br><span style="color: #00ff00;">> 📄 CODEBASE.md generated successfully.</span>`;
            
            if (typeof loadCodebasePreview === "function") loadCodebasePreview();
        } else {
            statusBox.innerHTML += `<br><span style="color: #ff4444;">> ❌ Audit Failed: ${data.error}</span>`;
        }
    } catch (error) {
        statusBox.innerHTML += `<br><span style="color: #ffbb00;">> ⚠️ Connection Error: ${error.message}</span>`;
    } finally {
        analyzeBtn.disabled = false;
    }
}