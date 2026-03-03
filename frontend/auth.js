// Multi-Agent SOC Dashboard — Auth Logic
// Client-side auth using localStorage (demo/prototype)

const USERS_KEY = 'soc_users';
const SESSION_KEY = 'soc_session';

// On load: if already authenticated, redirect to dashboard
(function checkSession() {
    if (localStorage.getItem(SESSION_KEY)) {
        window.location.replace('index.html');
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    document.getElementById('tab-login').addEventListener('click', () => showTab('login'));
    document.getElementById('tab-signup').addEventListener('click', () => showTab('signup'));

    // Form submissions
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('signup-form').addEventListener('submit', handleSignup);

    // Password toggle buttons
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const input = document.getElementById(targetId);
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🙈';
            } else {
                input.type = 'password';
                btn.textContent = '👁️';
            }
        });
    });
});

function showTab(tab) {
    const loginPanel = document.getElementById('login-panel');
    const signupPanel = document.getElementById('signup-panel');
    const tabLogin = document.getElementById('tab-login');
    const tabSignup = document.getElementById('tab-signup');

    if (tab === 'login') {
        loginPanel.classList.add('active');
        signupPanel.classList.remove('active');
        tabLogin.classList.add('active');
        tabSignup.classList.remove('active');
    } else {
        signupPanel.classList.add('active');
        loginPanel.classList.remove('active');
        tabSignup.classList.add('active');
        tabLogin.classList.remove('active');
    }

    // Clear messages when switching tabs
    clearMessages();
}

function handleLogin(e) {
    e.preventDefault();
    clearMessages();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showError('login-error', 'Please fill in all fields.');
        return;
    }

    const users = getUsers();
    const user = users.find(u => u.username === username && u.password === hashSimple(password));

    if (!user) {
        showError('login-error', 'Invalid username or password.');
        shakeForm('login-form');
        return;
    }

    // Set session
    localStorage.setItem(SESSION_KEY, JSON.stringify({ username: user.username, email: user.email, loginTime: Date.now() }));
    showSuccess('login-success', `Welcome back, ${user.username}! Redirecting...`);

    setTimeout(() => {
        window.location.replace('index.html');
    }, 1200);
}

function handleSignup(e) {
    e.preventDefault();
    clearMessages();

    const username = document.getElementById('signup-username').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirm = document.getElementById('signup-confirm').value;

    if (!username || !email || !password || !confirm) {
        showError('signup-error', 'Please fill in all fields.');
        return;
    }

    if (username.length < 3) {
        showError('signup-error', 'Username must be at least 3 characters.');
        return;
    }

    if (!isValidEmail(email)) {
        showError('signup-error', 'Please enter a valid email address.');
        return;
    }

    if (password.length < 6) {
        showError('signup-error', 'Password must be at least 6 characters.');
        return;
    }

    if (password !== confirm) {
        showError('signup-error', 'Passwords do not match.');
        shakeForm('signup-form');
        return;
    }

    const users = getUsers();
    if (users.find(u => u.username === username)) {
        showError('signup-error', 'Username already taken. Please choose another.');
        return;
    }
    if (users.find(u => u.email === email)) {
        showError('signup-error', 'Email already registered. Try logging in.');
        return;
    }

    // Store user
    users.push({ username, email, password: hashSimple(password), createdAt: Date.now() });
    localStorage.setItem(USERS_KEY, JSON.stringify(users));

    // Set session
    localStorage.setItem(SESSION_KEY, JSON.stringify({ username, email, loginTime: Date.now() }));
    showSuccess('signup-success', `Account created! Welcome, ${username}. Redirecting...`);

    setTimeout(() => {
        window.location.replace('index.html');
    }, 1300);
}

// --- Helpers ---

function getUsers() {
    try {
        return JSON.parse(localStorage.getItem(USERS_KEY)) || [];
    } catch {
        return [];
    }
}

function showError(id, msg) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = '⚠ ' + msg;
        el.style.display = 'block';
    }
}

function showSuccess(id, msg) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = '✓ ' + msg;
        el.style.display = 'block';
    }
}

function clearMessages() {
    document.querySelectorAll('.auth-error, .auth-success').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });
}

function shakeForm(formId) {
    const form = document.getElementById(formId);
    form.classList.add('shake');
    setTimeout(() => form.classList.remove('shake'), 500);
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Very simple one-way hash (not cryptographic — for demo only)
function hashSimple(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const ch = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + ch;
        hash |= 0;
    }
    return hash.toString(16);
}
