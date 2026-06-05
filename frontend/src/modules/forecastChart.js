// Line/area chart of the projected cumulative balance, drawn as inline SVG.
export function initForecastChart() {
    const container = document.getElementById("forecast-chart");
    const dataEl = document.getElementById("forecast-data");
    if (!container || !dataEl) return;

    let rows;
    try {
        rows = JSON.parse(dataEl.textContent);
    } catch {
        return;
    }
    if (!Array.isArray(rows) || rows.length === 0) return;

    const W = 320;
    const H = 140;
    const padX = 18;
    const padTop = 16;
    const padBottom = 26;
    const plotH = H - padTop - padBottom;

    const values = rows.map((r) => r.value);
    const vmin = Math.min(0, ...values);
    const vmax = Math.max(0, ...values);
    const range = vmax - vmin || 1;

    const x = (i) => (rows.length === 1 ? W / 2 : padX + (i / (rows.length - 1)) * (W - 2 * padX));
    const y = (v) => padTop + (1 - (v - vmin) / range) * plotH;
    const zeroY = y(0);

    const points = rows.map((r, i) => [x(i), y(r.value)]);
    const line = points.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
    const area = `${line} L${points[points.length - 1][0].toFixed(1)} ${zeroY.toFixed(1)} L${points[0][0].toFixed(1)} ${zeroY.toFixed(1)} Z`;

    const dots = points
        .map((p) => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="3" fill="#fff" stroke="#EC4899" stroke-width="2"/>`)
        .join("");
    const labels = rows
        .map((r, i) => `<text x="${x(i).toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="9" fill="#8B7A8E">${r.label}</text>`)
        .join("");

    container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" class="w-full">
  <defs>
    <linearGradient id="forecast-area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#EC4899" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#8B5CF6" stop-opacity="0.02"/>
    </linearGradient>
    <linearGradient id="forecast-line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#EC4899"/>
      <stop offset="1" stop-color="#8B5CF6"/>
    </linearGradient>
  </defs>
  <line x1="${padX}" y1="${zeroY.toFixed(1)}" x2="${W - padX}" y2="${zeroY.toFixed(1)}" stroke="#2A1A36" stroke-opacity="0.12" stroke-dasharray="3 3"/>
  <path d="${area}" fill="url(#forecast-area)"/>
  <path d="${line}" fill="none" stroke="url(#forecast-line)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  ${dots}
  ${labels}
</svg>`;
}
