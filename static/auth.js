/* Shared behaviour for the Darsio authentication pages. */
(function () {
    "use strict";

    // Smooth page-exit for internal navigation links marked with data-transition.
    document.addEventListener("click", function (e) {
        const link = e.target.closest("a[data-transition]");
        if (!link) return;

        const href = link.getAttribute("href");
        if (!href || href.startsWith("#")) return;

        e.preventDefault();
        document.body.classList.add("page-leave");
        window.setTimeout(function () {
            window.location.href = href;
        }, 190);
    });

    // Password visibility toggles.
    document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const targetId = btn.getAttribute("data-toggle-password");
            const input = document.getElementById(targetId);
            if (!input) return;

            const reveal = input.type === "password";
            input.type = reveal ? "text" : "password";
            btn.classList.toggle("showing", reveal);
        });
    });

    // Lightweight toast (e.g. "coming soon" hints).
    let toastEl = null;
    let toastTimer = null;

    window.showAuthToast = function (message) {
        if (!toastEl) {
            toastEl = document.createElement("div");
            toastEl.className = "toast";
            document.body.appendChild(toastEl);
        }

        toastEl.textContent = message;
        toastEl.classList.add("show");

        if (toastTimer) window.clearTimeout(toastTimer);
        toastTimer = window.setTimeout(function () {
            toastEl.classList.remove("show");
        }, 2600);
    };
})();
