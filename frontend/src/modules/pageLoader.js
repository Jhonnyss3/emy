// Top page-loading bar: shows progress on internal navigation and form submits.
export function initPageLoader() {
    const loader = document.getElementById("page-loader");
    const bar = document.getElementById("page-loader-bar");
    if (!loader || !bar) return;

    let timer;

    function start() {
        clearInterval(timer);
        loader.style.opacity = "1";
        bar.style.width = "0%";
        requestAnimationFrame(() => {
            bar.style.width = "75%";
        });
        // Creep toward 90% while the next page loads.
        timer = setInterval(() => {
            const w = parseFloat(bar.style.width) || 0;
            if (w < 90) bar.style.width = w + (90 - w) * 0.15 + "%";
        }, 400);
    }

    function done() {
        clearInterval(timer);
        bar.style.width = "100%";
        loader.style.opacity = "0";
        setTimeout(() => {
            bar.style.width = "0%";
        }, 300);
    }

    document.addEventListener("click", (e) => {
        const a = e.target.closest("a");
        if (!a) return;
        const href = a.getAttribute("href");
        if (!href || href.charAt(0) === "#") return;
        if (a.target === "_blank" || a.hasAttribute("download")) return;
        if (a.protocol === "mailto:" || a.protocol === "tel:") return;
        if (a.origin !== window.location.origin) return;
        if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey) return;
        start();
    });

    document.addEventListener("submit", () => start());

    // Finish on first paint and when restored from the back/forward cache.
    window.addEventListener("pageshow", () => done());
}
