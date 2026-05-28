async function loadExecutions() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    try {
        const executions = await fetchAPI('/executions');
        renderExecutions(executions);
    } catch (err) {
        console.error(err);
        document.getElementById('executionsTable').innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-red-500">Failed to load executions</td></tr>';
    }
}

function renderExecutions(executions) {
    const tbody = document.getElementById('executionsTable');
    if (!executions.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No executions yet.</td></tr>';
        return;
    }
    tbody.innerHTML = executions.map(exec => {
        let duration = '-';
        if (exec.completed_at) {
            const start = new Date(exec.started_at);
            const end = new Date(exec.completed_at);
            if (!isNaN(start) && !isNaN(end)) {
                duration = ((end - start) / 1000).toFixed(1) + 's';
            }
        }
        return `
            <tr>
                <td class="px-6 py-4">${exec.workflow_name || (exec.workflow_id ? exec.workflow_id.slice(0,8) : '-')}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 text-xs rounded-full ${exec.status === 'completed' ? 'bg-green-100 text-green-800' : exec.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}">${exec.status}</span>
                </td>
                <td class="px-6 py-4">${new Date(exec.started_at).toLocaleString()}</td>
                <td class="px-6 py-4">${duration}</td>
                <td class="px-6 py-4 text-red-600">${exec.errors?.length || 0}</td>
            </tr>
        `;
    }).join('');
}

loadExecutions();