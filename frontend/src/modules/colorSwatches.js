// Preset color swatches that set the category color picker on click.
export function initColorSwatches() {
    const picker = document.getElementById("id_color");
    if (!picker) return;

    document.querySelectorAll(".color-swatch").forEach((btn) => {
        btn.addEventListener("click", () => {
            picker.value = btn.dataset.color;
        });
    });
}
