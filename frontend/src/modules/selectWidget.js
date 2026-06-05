// Enhance every native <select> into a styled dropdown widget, keeping the
// native element as the source of truth (form submit and change events).
const SVG_NS = "http://www.w3.org/2000/svg";

export function initSelectWidget() {
    document.querySelectorAll("select").forEach(enhance);
}

function enhance(select) {
    if (select.dataset.enhanced) return;
    select.dataset.enhanced = "true";

    const wrapper = document.createElement("div");
    wrapper.className = "relative";
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);

    select.classList.add("sr-only");
    select.setAttribute("tabindex", "-1");
    select.setAttribute("aria-hidden", "true");

    const chevron = makeChevron();
    const label = document.createElement("span");
    label.className = "flex min-w-0 items-center gap-2 truncate";

    const button = document.createElement("button");
    button.type = "button";
    button.className = `${select.className.replace("sr-only", "").trim()} flex items-center justify-between gap-2 text-left`;
    button.setAttribute("aria-haspopup", "listbox");
    button.setAttribute("aria-expanded", "false");
    button.append(label, chevron);

    const panel = document.createElement("div");
    panel.className = "absolute z-30 mt-2 hidden max-h-60 w-full overflow-y-auto rounded-2xl bg-emy-surface p-1.5 shadow-card ring-1 ring-emy-line";
    panel.setAttribute("role", "listbox");

    const isOpen = () => !panel.classList.contains("hidden");
    const open = () => {
        panel.classList.remove("hidden");
        button.setAttribute("aria-expanded", "true");
        chevron.classList.add("rotate-180");
    };
    const close = () => {
        panel.classList.add("hidden");
        button.setAttribute("aria-expanded", "false");
        chevron.classList.remove("rotate-180");
    };

    const renderLabel = (target, option) => {
        target.replaceChildren();
        if (option && option.dataset.color) {
            const dot = document.createElement("span");
            dot.className = "h-2.5 w-2.5 shrink-0 rounded-full";
            dot.style.background = option.dataset.color;
            target.appendChild(dot);
        }
        const text = document.createElement("span");
        text.className = "truncate";
        text.textContent = option ? option.textContent : "";
        target.appendChild(text);
    };

    Array.from(select.options).forEach((option) => {
        const item = document.createElement("button");
        item.type = "button";
        item.setAttribute("role", "option");
        item.className = "flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-semibold text-emy-ink-soft transition hover:bg-emy-bg";
        renderLabel(item, option);
        item.addEventListener("click", () => {
            select.value = option.value;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            renderLabel(label, option);
            close();
        });
        panel.appendChild(item);
    });

    // Dynamic lists always offer a "create new" action at the bottom.
    if (select.dataset.createUrl) {
        const create = document.createElement("a");
        create.href = select.dataset.createUrl;
        create.className = "mt-1 flex w-full items-center gap-2 rounded-xl border-t border-emy-line px-3 py-2 text-sm font-bold text-emy-pink-600 transition hover:bg-emy-bg";
        const plus = document.createElement("span");
        plus.className = "grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emy-pink-100 text-emy-pink-600";
        plus.appendChild(makePlus());
        const text = document.createElement("span");
        text.textContent = select.dataset.createLabel || "Criar novo";
        create.append(plus, text);
        panel.appendChild(create);
    }

    wrapper.append(button, panel);

    button.addEventListener("click", () => (isOpen() ? close() : open()));
    document.addEventListener("click", (event) => {
        if (!wrapper.contains(event.target)) close();
    });

    renderLabel(label, select.options[select.selectedIndex]);
}

function makeChevron() {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 20 20");
    svg.setAttribute("fill", "currentColor");
    svg.setAttribute("class", "h-4 w-4 shrink-0 text-emy-ink-mute transition");
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("fill-rule", "evenodd");
    path.setAttribute("clip-rule", "evenodd");
    path.setAttribute("d", "M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.17l3.71-3.94a.75.75 0 1 1 1.08 1.04l-4.25 4.5a.75.75 0 0 1-1.08 0l-4.25-4.5a.75.75 0 0 1 .02-1.06Z");
    svg.appendChild(path);
    return svg;
}

function makePlus() {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "3");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("class", "h-3 w-3");
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", "M12 5v14M5 12h14");
    svg.appendChild(path);
    return svg;
}
