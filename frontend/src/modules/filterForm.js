// Auto-submit a filter form when a tagged control changes (selects, radios).
export function initFilterForm() {
    document.querySelectorAll("[data-autosubmit]").forEach((el) => {
        el.addEventListener("change", () => {
            const form = el.closest("form");
            if (!form) return;
            if (form.requestSubmit) form.requestSubmit();
            else form.submit();
        });
    });
}
