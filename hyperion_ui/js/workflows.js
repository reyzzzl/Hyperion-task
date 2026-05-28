async function loadWorkflows() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    try {
        const workflows = await fetchAPI('/workflows');
        renderWorkflows(workflows);
    } catch (err) {
        console.error(err);
        document.getElementById('workflowsTable').innerHTML = '<tr><td colspan="4" class="px-6 py-4 text-center text-red-500">Failed to load workflows</td></tr>';
    }
}

function renderWorkflows(workflows) {
    const tbody = document.getElementById('workflowsTable');
    if (!workflows.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No workflows found. Create one!</td></tr>';
        return;
    }
    tbody.innerHTML = workflows.map(wf => `
        <tr>
            <td class="px-6 py-4">${wf.name}</td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 text-xs rounded-full ${wf.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">${wf.status}</span>
            </td>
            <td class="px-6 py-4">${new Date(wf.updated_at).toLocaleDateString()}</td>
            <td class="px-6 py-4 space-x-2">
                <a href="workflow-editor.html?id=${wf.workflow_id}" class="text-blue-600 hover:underline">Edit</a>
                <button onclick="deleteWorkflow('${wf.workflow_id}')" class="text-red-600 hover:underline">Delete</button>
            </td>
        </tr>
    `).join('');
}

async function deleteWorkflow(id) {
    if (!confirm('Are you sure?')) return;
    try {
        await fetchAPI(`/workflows/${id}`, { method: 'DELETE' });
        loadWorkflows();
    } catch (err) {
        alert('Delete failed: ' + err.message);
    }
}

loadWorkflows();