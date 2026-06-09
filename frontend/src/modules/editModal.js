// Per-transaction edit modal (desktop): the edit links open the matching modal
// instead of navigating; on mobile they fall back to the form page. Submits go
// over fetch — success reloads the page, validation errors render in the modal.
export function initEditModal() {
    const modals = Array.from(document.querySelectorAll("[data-edit-modal]"));
    if (!modals.length) return;

    const isDesktop = () => window.matchMedia("(min-width: 1024px)").matches;
    const close = (modal) => {
        modal.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
    };
    const closeAll = () => modals.forEach(close);
    const open = (modal) => {
        closeAll();
        modal.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");
    };

    document.querySelectorAll("[data-open-edit]").forEach((trigger) => {
        trigger.addEventListener("click", (event) => {
            if (!isDesktop()) return; // mobile keeps the full-page form
            const modal = document.querySelector(
                `[data-edit-modal="${trigger.dataset.openEdit}"]`
            );
            if (!modal) return;
            event.preventDefault();
            open(modal);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeAll();
    });

    modals.forEach((modal) => {
        modal.querySelectorAll("[data-edit-close]").forEach((el) =>
            el.addEventListener("click", () => close(modal))
        );

        modal.querySelectorAll("[data-edit-form]").forEach((form) => {
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
    });
}

function clearErrors(form) {
    form.querySelectorAll("[data-edit-error]").forEach((slot) => {
        slot.textContent = "";
        if (slot.dataset.editError === "__all__") slot.classList.add("hidden");
    });
}

function showErrors(form, errors) {
    Object.entries(errors).forEach(([field, messages]) => {
        const slot = form.querySelector(`[data-edit-error="${field}"]`);
        if (!slot) return;
        slot.textContent = messages.join(" ");
        if (field === "__all__") slot.classList.remove("hidden");
    });
}
