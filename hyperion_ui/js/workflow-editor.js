const urlParams = new URLSearchParams(window.location.search);
const workflowId = urlParams.get('id');

async function loadWorkflow() {
    if (!workflowId) return;
    try {
        const workflow = await fetchAPI(`/workflows/${workflowId}`);
        document.getElementById('workflowId').value = workflow.workflow_id;
        document.getElementById('name').value = workflow.name;
        document.getElementById('description').value = workflow.description || '';
        document.getElementById('definition').value = JSON.stringify({
            nodes: workflow.nodes || [],
            edges: workflow.edges || []
        }, null, 2);
    } catch (err) {
        console.error(err);
        alert('Failed to load workflow: ' + err.message);
    }
}

document.getElementById('workflowForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const description = document.getElementById('description').value;
    let definition;
    try {
        definition = JSON.parse(document.getElementById('definition').value);
    } catch (err) {
        alert('Invalid JSON definition: ' + err.message);
        return;
    }
    const payload = {
        name: name,
        description: description,
        nodes: definition.nodes || [],
        edges: definition.edges || []
    };
    try {
        if (workflowId) {
            await fetchAPI(`/workflows/${workflowId}`, { method: 'PUT', body: payload });
        } else {
            await fetchAPI('/workflows', { method: 'POST', body: payload });
        }
        window.location.href = '/workflows.html';
    } catch (err) {
        alert('Save failed: ' + err.message);
    }
});

loadWorkflow();