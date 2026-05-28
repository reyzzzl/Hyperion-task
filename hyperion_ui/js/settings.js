async function loadSettings() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    const user = getCurrentUser();
    if (user) {
        document.getElementById('profileName').value = user.name || '';
        document.getElementById('profileEmail').value = user.email || '';
    }
    await loadApiKeys();
}

async function loadApiKeys() {
    try {
        const keys = await fetchAPI('/api-keys');
        const container = document.getElementById('apiKeysList');
        if (!keys.length) {
            container.innerHTML = '<p class="text-gray-500">No API keys yet.</p>';
            return;
        }
        container.innerHTML = keys.map(key => `
            <div class="flex justify-between items-center border-b pb-2">
                <div>
                    <div class="font-mono text-sm">${key.key_id.slice(0,8)}...</div>
                    <div class="text-xs text-gray-500">Scopes: ${key.scopes?.join(', ') || 'all'}</div>
                    <div class="text-xs text-gray-500">Expires: ${key.expires_at ? new Date(key.expires_at).toLocaleDateString() : 'never'}</div>
                </div>
                <button onclick="revokeApiKey('${key.key_id}')" class="text-red-600 text-sm">Revoke</button>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
        document.getElementById('apiKeysList').innerHTML = '<p class="text-red-500">Failed to load API keys</p>';
    }
}

async function revokeApiKey(keyId) {
    if (!confirm('Revoke this API key?')) return;
    try {
        await fetchAPI(`/api-keys/${keyId}`, { method: 'DELETE' });
        await loadApiKeys();
    } catch (err) {
        alert('Revoke failed: ' + err.message);
    }
}

document.getElementById('updateProfileBtn')?.addEventListener('click', async () => {
    const name = document.getElementById('profileName').value;
    const email = document.getElementById('profileEmail').value;
    try {
        await fetchAPI('/users/me', { method: 'PUT', body: { name, email } });
        const currentUser = getCurrentUser();
        const updatedUser = { ...currentUser, name, email };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        alert('Profile updated');
    } catch (err) {
        alert('Update failed: ' + err.message);
    }
});

document.getElementById('generateApiKeyBtn')?.addEventListener('click', async () => {
    try {
        const data = await fetchAPI('/api-keys', { method: 'POST', body: {} });
        alert(`New API Key: ${data.key}\nMake sure to copy it now.`);
        await loadApiKeys();
    } catch (err) {
        alert('Generation failed: ' + err.message);
    }
});

loadSettings();