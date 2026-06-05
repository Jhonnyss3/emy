// Close the scope dropdown (<details>) when clicking outside of it.
export function initScopeMenu() {
    const scopeMenu = document.getElementById("scope-menu");
    if (!scopeMenu) return;

    document.addEventListener("click", (e) => {
        if (scopeMenu.open && !scopeMenu.contains(e.target)) {
            scopeMenu.open = false;
        }
    });
}
