async function loadDashboard() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    try {
        const stats = await fetchAPI('/stats');
        const executions = await fetchAPI('/executions?limit=5');
        const workflows = await fetchAPI('/workflows?limit=5');
        renderStats(stats);
        renderRecentExecutions(executions);
        renderRecentWorkflows(workflows);
    } catch (err) {
        console.error(err);
        document.getElementById('stats').innerHTML = '<div class="col-span-4 text-center text-red-500">Failed to load dashboard</div>';
    }
}

function renderStats(stats) {
    const container = document.getElementById('stats');
    container.innerHTML = `
        <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div class="text-gray-500">Total Workflows</div>
            <div class="text-2xl font-bold">${stats.totalWorkflows || 0}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div class="text-gray-500">Active Workflows</div>
            <div class="text-2xl font-bold">${stats.activeWorkflows || 0}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div class="text-gray-500">Total Executions</div>
            <div class="text-2xl font-bold">${stats.totalExecutions || 0}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div class="text-gray-500">Success Rate</div>
            <div class="text-2xl font-bold">${stats.successRate || 0}%</div>
        </div>
    `;
}

function renderRecentExecutions(executions) {
    const container = document.getElementById('recentExecutions');
    if (!executions.length) {
        container.innerHTML = '<h3 class="font-semibold mb-2">Recent Executions</h3><p class="text-gray-500">No executions yet.</p>';
        return;
    }
    container.innerHTML = `
        <h3 class="font-semibold mb-2">Recent Executions</h3>
        <div class="space-y-2">
            ${executions.map(exec => `
                <div class="flex justify-between items-center border-b pb-2">
                    <div>
                        <div class="font-medium">${exec.workflow_name || (exec.workflow_id ? exec.workflow_id.slice(0,8) : '-')}</div>
                        <div class="text-sm text-gray-500">${new Date(exec.started_at).toLocaleString()}</div>
                    </div>
                    <span class="px-2 py-1 text-xs rounded-full ${exec.status === 'completed' ? 'bg-green-100 text-green-800' : exec.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}">${exec.status}</span>
                </div>
            `).join('')}
        </div>
    `;
}

function renderRecentWorkflows(workflows) {
    const container = document.getElementById('recentWorkflows');
    if (!workflows.length) {
        container.innerHTML = '<h3 class="font-semibold mb-2">Recent Workflows</h3><p class="text-gray-500">No workflows yet.</p><a href="workflows.html" class="text-blue-600 text-sm mt-2 inline-block">Create one →</a>';
        return;
    }
    container.innerHTML = `
        <h3 class="font-semibold mb-2">Recent Workflows</h3>
        <div class="space-y-2">
            ${workflows.map(wf => `
                <div class="flex justify-between items-center border-b pb-2">
                    <div>
                        <div class="font-medium">${wf.name}</div>
                        <div class="text-sm text-gray-500">Updated ${new Date(wf.updated_at).toLocaleDateString()}</div>
                    </div>
                    <a href="workflow-editor.html?id=${wf.workflow_id}" class="text-blue-600 text-sm">Edit</a>
                </div>
            `).join('')}
        </div>
        <a href="workflows.html" class="text-blue-600 text-sm mt-2 inline-block">View all →</a>
    `;
}

loadDashboard();