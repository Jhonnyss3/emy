// Global launch modal (desktop): the launch buttons open it instead of
// navigating; on mobile they fall back to the form pages. Submits go over
// fetch — success reloads the page, validation errors render inside the modal.
export function initLaunchModal() {
    const modal = document.querySelector("[data-launch-modal]");
    if (!modal) return;

    const isDesktop = () => window.matchMedia("(min-width: 1024px)").matches;
    const open = () => {
        modal.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");
    };
    const close = () => {
        modal.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
    };

    document.querySelectorAll("[data-open-launch]").forEach((trigger) => {
        trigger.addEventListener("click", (event) => {
            if (!isDesktop()) return; // mobile keeps the full-page form
            event.preventDefault();
            open();
        });
    });

    modal.querySelectorAll("[data-launch-close]").forEach((el) =>
        el.addEventListener("click", close)
    );
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !modal.classList.contains("hidden")) close();
    });

    // Tabs
    const tabs = Array.from(modal.querySelectorAll("[data-launch-tab]"));
    const panels = Array.from(modal.querySelectorAll("[data-launch-panel]"));
    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const name = tab.dataset.launchTab;
            tabs.forEach((t) => t.setAttribute("data-active", String(t === tab)));
            panels.forEach((p) =>
                p.classList.toggle("hidden", p.dataset.launchPanel !== name)
            );
        });
    });

    // AJAX submit
    modal.querySelectorAll("[data-launch-form]").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            clearErrors(form);
            let data;
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });
                data = await response.json();
            } catch (error) {
                return;
            }
            if (data && data.ok) {
                window.location.reload();
            } else if (data) {
                showErrors(form, data.errors || {});
            }
        });
    });
}

function clearErrors(form) {
    form.querySelectorAll("[data-launch-error]").forEach((slot) => {
        slot.textContent = "";
        if (slot.dataset.launchError === "__all__") slot.classList.add("hidden");
    });
}

function showErrors(form, errors) {
    Object.entries(errors).forEach(([field, messages]) => {
        const slot = form.querySelector(`[data-launch-error="${field}"]`);
        if (!slot) return;
        slot.textContent = messages.join(" ");
        if (field === "__all__") slot.classList.remove("hidden");
    });
}
