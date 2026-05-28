const API_BASE = '/api';
let authToken = localStorage.getItem('access_token');

function setAuthToken(token) {
    authToken = token;
    if (token) {
        localStorage.setItem('access_token', token);
    } else {
        localStorage.removeItem('access_token');
    }
}

function getAuthToken() {
    return authToken;
}

async function fetchAPI(endpoint, options = {}) {
    const url = API_BASE + endpoint;
    const headers = {
        'Content-Type': 'application/json',
    };
    if (authToken) {
        headers['Authorization'] = 'Bearer ' + authToken;
    }
    if (options.headers) {
        Object.assign(headers, options.headers);
    }
    let body = options.body;
    if (body && typeof body === 'object' && !(body instanceof FormData) && !(body instanceof URLSearchParams)) {
        body = JSON.stringify(body);
    }
    try {
        const response = await fetch(url, {
            method: options.method || 'GET',
            headers: headers,
            body: body,
        });
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login.html';
            throw new Error('Session expired. Please login again.');
        }
        if (!response.ok) {
            let errorMsg = 'Request failed';
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorData.message || JSON.stringify(errorData);
            } catch (e) {
                errorMsg = response.statusText || 'Request failed';
            }
            throw new Error(errorMsg);
        }
        if (response.status === 204) return null;
        return await response.json();
    } catch (err) {
        if (err.message === 'Failed to fetch') {
            throw new Error('Cannot connect to server. Please check if backend is running.');
        }
        throw err;
    }
}