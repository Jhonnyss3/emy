// Styled date widget: a button shows the date as dd/mm/aaaa while a hidden
// input carries the ISO value (YYYY-MM-DD) the form submits. The popover draws
// a month calendar in plain JS — no native date input, no library.
const MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];
const WEEKDAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

export function initDateWidget() {
    document.querySelectorAll("[data-date-widget]").forEach(setup);
}

function pad(n) {
    return String(n).padStart(2, "0");
}

function parseISO(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || "");
    if (!match) return null;
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

function setup(root) {
    const input = root.querySelector("[data-date-input]");
    const toggle = root.querySelector("[data-date-toggle]");
    const label = root.querySelector("[data-date-label]");
    const panel = root.querySelector("[data-date-panel]");
    const title = root.querySelector("[data-date-title]");
    const grid = root.querySelector("[data-date-grid]");
    const weekdays = root.querySelector("[data-date-weekdays]");
    if (!input || !toggle || !label || !panel || !title || !grid) return;

    let selected = parseISO(input.value);
    const view = selected ? new Date(selected) : new Date();
    view.setDate(1);

    weekdays.replaceChildren(
        ...WEEKDAYS.map((name) => {
            const cell = document.createElement("span");
            cell.textContent = name;
            return cell;
        })
    );

    const renderLabel = () => {
        if (selected) {
            label.textContent =
                pad(selected.getDate()) + "/" + pad(selected.getMonth() + 1) + "/" + selected.getFullYear();
            label.classList.remove("text-emy-ink-mute");
        } else {
            label.textContent = "dd/mm/aaaa";
            label.classList.add("text-emy-ink-mute");
        }
    };

    const sameDay = (a, b) =>
        a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

    const renderGrid = () => {
        title.textContent = MONTHS[view.getMonth()] + " " + view.getFullYear();
        const today = new Date();
        const firstWeekday = view.getDay();
        const daysInMonth = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
        const cells = [];
        for (let i = 0; i < firstWeekday; i += 1) {
            const blank = document.createElement("span");
            cells.push(blank);
        }
        for (let day = 1; day <= daysInMonth; day += 1) {
            const date = new Date(view.getFullYear(), view.getMonth(), day);
            const cell = document.createElement("button");
            cell.type = "button";
            cell.textContent = String(day);
            cell.className =
                "grid h-9 place-items-center rounded-xl text-sm font-semibold transition hover:bg-emy-bg";
            if (sameDay(date, selected)) {
                cell.className += " bg-gradient-to-br from-emy-pink-500 to-emy-purple-500 text-white";
            } else if (sameDay(date, today)) {
                cell.className += " text-emy-pink-600 ring-1 ring-emy-pink-300";
            } else {
                cell.className += " text-emy-ink-soft";
            }
            cell.addEventListener("click", () => {
                selected = date;
                input.value = date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate());
                input.dispatchEvent(new Event("change", { bubbles: true }));
                renderLabel();
                close();
            });
            cells.push(cell);
        }
        grid.replaceChildren(...cells);
    };

    const open = () => {
        panel.classList.remove("hidden");
        toggle.setAttribute("aria-expanded", "true");
        renderGrid();
    };
    const close = () => {
        panel.classList.add("hidden");
        toggle.setAttribute("aria-expanded", "false");
    };
    const isOpen = () => !panel.classList.contains("hidden");

    toggle.addEventListener("click", () => (isOpen() ? close() : open()));
    root.querySelector("[data-date-prev]")?.addEventListener("click", () => {
        view.setMonth(view.getMonth() - 1);
        renderGrid();
    });
    root.querySelector("[data-date-next]")?.addEventListener("click", () => {
        view.setMonth(view.getMonth() + 1);
        renderGrid();
    });
    root.querySelector("[data-date-today]")?.addEventListener("click", () => {
        const today = new Date();
        selected = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        input.value = selected.getFullYear() + "-" + pad(selected.getMonth() + 1) + "-" + pad(selected.getDate());
        input.dispatchEvent(new Event("change", { bubbles: true }));
        view.setFullYear(today.getFullYear(), today.getMonth(), 1);
        renderLabel();
        close();
    });
    root.querySelector("[data-date-clear]")?.addEventListener("click", () => {
        selected = null;
        input.value = "";
        input.dispatchEvent(new Event("change", { bubbles: true }));
        renderLabel();
        close();
    });
    document.addEventListener("click", (event) => {
        if (!root.contains(event.target)) close();
    });

    renderLabel();
}
