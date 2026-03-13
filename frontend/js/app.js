const API = 'http://127.0.0.1:8003';
let CURRENT_REPO_PATH = localStorage.getItem('current_repo') || 'targets/jaffle_shop';
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
        // Normalize path for URL (convert backslashes to forward slashes)
        // Normalize path for URL (convert backslashes to forward slashes)
        const safeRepoPath = (CURRENT_REPO_PATH || 'targets/jaffle_shop').replace(/\\/g, '/');
        
        const res = await fetch(`${API}/api/agent/surveyor/graph?repo_path=${safeRepoPath}`);
        
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
        // Normalize path for URL (convert backslashes to forward slashes)
        const safeRepoPath = (CURRENT_REPO_PATH || 'targets/jaffle_shop').replace(/\\/g, '/');

        const res = await fetch(`${API}/api/agent/hydrologist/graph?repo_path=${safeRepoPath}`);
        const data = await res.json();
        
        console.log('Hydrologist raw elements:', data.elements?.length, 'elements');
        
        // ✅ Filter out invalid edges (null/undefined source or target)
        const validElements = data.elements.filter(el => {
            if (!el || !el.data) return false;
            
            // For edges, both source and target must exist and be non-empty
            if (el.data.source !== undefined && el.data.target !== undefined) {
                const src = el.data.source;
                const tgt = el.data.target;
                const isValid = src && tgt && 
                               String(src).trim() !== '' && 
                               String(tgt).trim() !== '';
                if (!isValid) {
                    console.warn('⚠️ Filtering invalid edge:', {source: src, target: tgt});
                }
                return isValid;
            }
            // For nodes, just need a valid id
            return el.data.id && String(el.data.id).trim() !== '';
        });
        
        console.log('✅ Valid elements after filter:', validElements.length, '(was', data.elements?.length, ')');
        
        if (hydrologistCy) hydrologistCy.destroy();
        
        hydrologistCy = cytoscape({
            container: document.getElementById('hydrologist-viz'),
            elements: validElements,  // ✅ Use filtered data
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
        console.log('✅ Hydrologist graph rendered');
        
    } catch (err) {
        console.error('Hydrologist error:', err);
        const viz = document.getElementById('hydrologist-viz');
        if (viz) viz.innerHTML = `<p class="error-state">Error: ${err.message}</p>`;
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
        console.error('purpose-list-content container not found');
        return;
    }
    
    // Show loading state
    container.innerHTML = '<div style="text-align:center;padding:2rem;color:#3498db">Loading purpose statements...</div>';
    
    try {
        // Get current repo path and normalize slashes for URL
        let repoPath = localStorage.getItem('current_repo') || 'targets/jaffle_shop';
        repoPath = repoPath.replace(/\\/g, '/');
        
        // Use the /full endpoint
        const response = await fetch(`/api/agent/semanticist/full?repo_path=${repoPath}`);
        const data = await response.json();
        
        console.log('Agent 3 API response:', data);
        
        // Handle API error
        if (!data.ok) {
            container.innerHTML = `<p style="color:#e74c3c">API Error: ${data.error || 'Unknown error'}</p>`;
            return;
        }
        
        // Extract purposes from response
        const purposes = data.purposes || data.result?.purpose_statements || {};
        
        // Handle empty purposes
        if (!purposes || Object.keys(purposes).length === 0) {
            container.innerHTML = `
                <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:1rem;border-radius:4px">
                    <strong>⚠️ No Purpose Statements</strong>
                    <p style="margin:0.5rem 0 0 0;color:#856404;font-size:0.9rem">
                        Semanticist may require an LLM API key, or no modules were analyzed.
                    </p>
                </div>
            `;
            console.log('ℹ️ No purposes found');
            return;
        }
        
        // ✅ RENDER THE PURPOSES (this was missing!)
        let html = '';
        for (const [moduleId, info] of Object.entries(purposes)) {
            const purpose = info.purpose_statement || info.purpose || 'No purpose generated';
            const hasDrift = info.has_drift || info.has_documentation_drift;
            const driftReason = info.drift_reason || 'Documentation contradicts implementation';
            const filePath = info.file_path || '';
            
            const borderColor = hasDrift ? '#ffc107' : '#007bff';
            const bgColor = hasDrift ? '#fffbeb' : '#ffffff';
            
            html += `<div class="card" style="background:${bgColor};border:1px solid #e0e0e0;border-left:4px solid ${borderColor};padding:1rem;margin-bottom:1rem;border-radius:6px">`;
            html += `<h4 style="margin:0 0 0.5rem 0;color:#1a1a2e;font-size:1.05rem">${moduleId}</h4>`;
            html += `<p style="margin:0 0 0.5rem 0;color:#333;line-height:1.5">${purpose}</p>`;
            if (filePath) {
                html += `<small style="color:#6c757d;display:block;margin-bottom:0.5rem">📁 ${filePath}</small>`;
            }
            if (hasDrift) {
                html += `<div style="background:#fff3cd;border-left:3px solid #ffc107;padding:0.5rem 0.75rem;border-radius:4px;margin-top:0.5rem">`;
                html += `<strong style="color:#856404;font-size:0.9rem">⚠️ Documentation Drift</strong>`;
                html += `<p style="margin:0.25rem 0 0 0;color:#856404;font-size:0.9rem">${driftReason}</p>`;
                html += `</div>`;
            }
            html += `</div>`;
        }
        container.innerHTML = html;
        console.log('✅ Agent 3 rendered:', Object.keys(purposes).length, 'modules');
        
    } catch (error) {
        // ✅ CATCH BLOCK (this was missing!)
        console.error('❌ Agent 3 error:', error);
        container.innerHTML = `<p style="color:#e74c3c;background:#fdeaea;padding:1rem;border-radius:6px">Error: ${error.message}</p>`;
    }
}
// ✅ Function closing brace (this was missing!)

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

// ============================================================================
// OVERVIEW: Repo Analysis Handler
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyze-btn');
    const repoInput = document.getElementById('repo-url-input');
    const statusDiv = document.getElementById('repo-status');
    const logsDiv = document.getElementById('analysis-logs');
    const logsSection = document.getElementById('analysis-logs-section');
    const resultsSection = document.getElementById('agent-results-section');
    
    if (analyzeBtn && repoInput) {
        analyzeBtn.addEventListener('click', async function() {
            const repoUrl = repoInput.value.trim();
            if (!repoUrl) {
                repoInput.focus();
                return;
            }
            
            // UI: Show loading state
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '⏳ Analyzing...';
            statusDiv.style.display = 'block';
            statusDiv.style.background = '#e3f2fd';
            statusDiv.style.color = '#1976d2';
            statusDiv.innerHTML = '🔄 Cloning repository...';
            logsSection.style.display = 'block';
            logsDiv.innerHTML = '<div>🔄 Connecting to backend...</div>';
            resultsSection.style.display = 'none';
            
            try {
                // Call backend API
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({repo_url: repoUrl})
                });
                
                const result = await response.json();
                
                if (!result.ok) {
                    throw new Error(result.error || 'Analysis failed');
                }

                // Save current repo path for graph tabs
                if (result.local_path) {
                    CURRENT_REPO_PATH = result.local_path;
                    localStorage.setItem('current_repo', result.local_path);
                    console.log('📁 Current repo saved:', result.local_path);
                }
                
                // Update progress logs
                if (result.progress_log && logsDiv) {
                    logsDiv.innerHTML = '';
                    for (const entry of result.progress_log) {
                        const icon = entry.level === 'success' ? '✅' : entry.level === 'error' ? '❌' : 'ℹ️';
                        logsDiv.innerHTML += `<div>[${entry.timestamp}] ${icon} ${entry.message}</div>`;
                    }
                    logsDiv.scrollTop = logsDiv.scrollHeight;
                }
                
                // Update stats
                if (result.stats) {
                    document.getElementById('stat-nodes').textContent = result.stats.total_nodes || 0;
                    document.getElementById('stat-edges').textContent = result.stats.total_edges || 0;
                    document.getElementById('stat-modules').textContent = result.stats.semanticist?.modules || 0;
                    document.getElementById('stat-drift').textContent = result.stats.drift_count || 0;
                    
                    // Agent 1
                    document.getElementById('a1-nodes').textContent = result.stats.surveyor?.nodes || '-';
                    document.getElementById('a1-edges').textContent = result.stats.surveyor?.edges || '-';
                    // Agent 2
                    document.getElementById('a2-nodes').textContent = result.stats.hydrologist?.nodes || '-';
                    document.getElementById('a2-edges').textContent = result.stats.hydrologist?.edges || '-';
                    // Agent 3
                    document.getElementById('a3-modules').textContent = result.stats.semanticist?.modules || '-';
                    document.getElementById('a3-drift').textContent = result.stats.drift_count || '-';
                }
                
                // Show results section
                resultsSection.style.display = 'block';
                
                // Update status
                statusDiv.style.background = '#e8f5e9';
                statusDiv.style.color = '#2e7d32';
                statusDiv.innerHTML = '✅ Analysis complete! Scroll down for results.';
                
                console.log('✅ Analysis complete:', result);
                
            } catch (error) {
                console.error('❌ Analysis error:', error);
                statusDiv.style.background = '#ffebee';
                statusDiv.style.color = '#c62828';
                statusDiv.innerHTML = '❌ Error: ' + error.message;
                if (logsDiv) logsDiv.innerHTML += `<div style="color:#ef5350">❌ ${error.message}</div>`;
            } finally {
                // Reset button
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = 'Analyze';
            }
        });
        
        // Allow Enter key to trigger analysis
        repoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeBtn.click();
        });
        
        console.log('✅ Overview analyze button listener attached');
    }
});