// Donut chart of expenses by category, drawn from the dashboard's by_category data.
const SVG_NS = "http://www.w3.org/2000/svg";

export function initCategoryDonut() {
    const container = document.getElementById("category-donut");
    const dataEl = document.getElementById("category-data");
    if (!container || !dataEl) return;

    let rows;
    try {
        rows = JSON.parse(dataEl.textContent);
    } catch {
        return;
    }
    if (!Array.isArray(rows) || rows.length === 0) return;

    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 36 36");
    svg.setAttribute("class", "h-32 w-32 -rotate-90");

    svg.appendChild(makeCircle("#F6E9E4", "100 0", 0));

    let cumulative = 0;
    rows.forEach((row) => {
        const pct = parseFloat(row.percent);
        if (!pct) return;
        svg.appendChild(makeCircle(row.color || "#8B5CF6", `${pct} ${100 - pct}`, -cumulative));
        cumulative += pct;
    });

    container.replaceChildren(svg);
}

function makeCircle(stroke, dasharray, dashoffset) {
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", "18");
    circle.setAttribute("cy", "18");
    circle.setAttribute("r", "15.915");
    circle.setAttribute("fill", "none");
    circle.setAttribute("stroke", stroke);
    circle.setAttribute("stroke-width", "4");
    circle.setAttribute("stroke-dasharray", dasharray);
    circle.setAttribute("stroke-dashoffset", dashoffset);
    return circle;
}
