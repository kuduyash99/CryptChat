(function () {
    const storageKey = "cryptchat-theme";
    const root = document.documentElement;

    function savedTheme() {
        try {
            return localStorage.getItem(storageKey) === "dark" ? "dark" : "light";
        } catch (error) {
            return "light";
        }
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;
        const button = document.getElementById("theme-toggle");
        if (button) {
            button.textContent = theme === "dark" ? "Light mode" : "Dark mode";
            button.setAttribute("aria-pressed", String(theme === "dark"));
        }
    }

    applyTheme(savedTheme());

    const button = document.createElement("button");
    button.type = "button";
    button.id = "theme-toggle";
    button.className = "btn theme-toggle";
    button.addEventListener("click", function () {
        const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
        try {
            localStorage.setItem(storageKey, nextTheme);
        } catch (error) {
            // The current page still changes theme when storage is unavailable.
        }
        applyTheme(nextTheme);
    });

    function addToggle() {
        document.body.appendChild(button);
        applyTheme(savedTheme());
    }

    if (document.body) {
        addToggle();
    } else {
        document.addEventListener("DOMContentLoaded", addToggle, { once: true });
    }
})();
