// Dark-only theme manager for app dashboards.
// Login page uses light theme to match royalpark.az marketing (see login.css).
(function () {
    "use strict";

    function isLoginPage() {
        var raw = window.location.pathname || "";
        // Нормализуем: "" и "/" — корень; server.js отдаёт тот же login.html, что и /login.html
        var p = raw.replace(/\/+$/, "") || "/";
        if (p === "/") return true;
        if (/\/login\.html$/i.test(raw)) return true;
        if (/^\/login$/i.test(p)) return true;
        return false;
    }

    function enforceDarkTheme() {
        if (isLoginPage()) {
            document.documentElement.setAttribute("data-theme", "light");
            document.body?.setAttribute("data-theme", "light");
            return;
        }
        document.documentElement.setAttribute("data-theme", "dark");
        document.body?.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
        // Remove any obsolete toggle button that can remain in DOM.
        document.querySelectorAll(".theme-toggle").forEach((el) => el.remove());
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", enforceDarkTheme);
    } else {
        enforceDarkTheme();
    }

    window.ThemeManager = {
        init: enforceDarkTheme,
    };
})();

