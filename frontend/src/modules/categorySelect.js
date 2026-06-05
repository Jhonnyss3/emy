// Custom category dropdown: color-dot options, filtered by the form's selected type.
export function initCategorySelect() {
    document.querySelectorAll("[data-category-select]").forEach(setup);
}

function setup(root) {
    const input = root.querySelector("[data-category-input]");
    const toggle = root.querySelector("[data-category-toggle]");
    const label = root.querySelector("[data-category-label]");
    const panel = root.querySelector("[data-category-panel]");
    const chevron = root.querySelector("[data-category-chevron]");
    const options = Array.from(root.querySelectorAll("[data-category-option]"));
    if (!input || !toggle || !label || !panel) return;

    const isOpen = () => !panel.classList.contains("hidden");
    const open = () => {
        panel.classList.remove("hidden");
        toggle.setAttribute("aria-expanded", "true");
        if (chevron) chevron.classList.add("rotate-180");
    };
    const close = () => {
        panel.classList.add("hidden");
        toggle.setAttribute("aria-expanded", "false");
        if (chevron) chevron.classList.remove("rotate-180");
    };

    const setSelected = (opt) => {
        if (opt) {
            input.value = opt.dataset.value;
            const dot = document.createElement("span");
            dot.className = "h-2.5 w-2.5 shrink-0 rounded-full";
            dot.style.background = opt.dataset.color;
            const name = document.createElement("span");
            name.className = "truncate font-semibold";
            name.textContent = opt.dataset.name;
            label.replaceChildren(dot, name);
        } else {
            input.value = "";
            const placeholder = document.createElement("span");
            placeholder.className = "text-emy-ink-mute";
            placeholder.textContent = "Selecione a categoria";
            label.replaceChildren(placeholder);
        }
    };

    toggle.addEventListener("click", () => (isOpen() ? close() : open()));
    options.forEach((opt) => {
        opt.addEventListener("click", () => {
            setSelected(opt);
            close();
        });
    });
    document.addEventListener("click", (event) => {
        if (!root.contains(event.target)) close();
    });

    // Filter options by the form's selected type, clearing an incompatible choice.
    const form = root.closest("form");
    const typeInputs = form ? Array.from(form.querySelectorAll('input[name="type"]')) : [];
    const currentType = () => {
        const checked = typeInputs.find((i) => i.checked);
        return checked ? checked.value : null;
    };
    const applyTypeFilter = () => {
        const type = currentType();
        options.forEach((opt) => {
            opt.classList.toggle("hidden", Boolean(type) && opt.dataset.type !== type);
        });
        const selected = options.find((opt) => opt.dataset.value === input.value);
        if (selected && type && selected.dataset.type !== type) setSelected(null);
    };
    typeInputs.forEach((i) => i.addEventListener("change", applyTypeFilter));

    const initial = options.find((opt) => opt.dataset.value === input.value);
    if (initial) setSelected(initial);
    applyTypeFilter();
}
