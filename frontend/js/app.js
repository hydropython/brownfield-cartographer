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




