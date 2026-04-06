// Dark-only theme manager for app dashboards.
// Login page uses light theme to match royalpark.az marketing (see login.css).
(function () {
    "use strict";

    function isLoginPage() {
        var p = window.location.pathname || "";
        return /\/login\.html$/i.test(p) || /\/login\/?$/i.test(p);
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

