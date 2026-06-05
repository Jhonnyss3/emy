// Toggle the password field visibility on the login screen.
export function initPasswordToggle() {
    const btn = document.getElementById("toggle-password");
    const input = document.getElementById("id_password");
    if (!btn || !input) return;

    btn.addEventListener("click", () => {
        input.type = input.type === "password" ? "text" : "password";
    });
}
