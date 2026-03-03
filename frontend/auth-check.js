// Auth guard — runs immediately before DOM loads
// Redirects unauthenticated users to auth.html
(function () {
    const session = localStorage.getItem('soc_session');
    if (!session) {
        const path = window.location.pathname;
        if (!path.endsWith('auth.html')) {
            window.location.replace('auth.html');
        }
    }
})();
