// Dark-only theme manager.
// The project supports a single visual mode: dark.
(function () {
    "use strict";

    function enforceDarkTheme() {
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

