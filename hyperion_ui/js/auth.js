async function login(email, password) {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password }),
    });
    if (!response.ok) {
        let errorMsg = 'Login failed';
        try {
            const errorData = await response.json();
            errorMsg = errorData.detail || errorData.message || 'Login failed';
        } catch (e) {}
        throw new Error(errorMsg);
    }
    const data = await response.json();
    setAuthToken(data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
}

function logout() {
    setAuthToken(null);
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function isAuthenticated() {
    return !!getAuthToken();
}