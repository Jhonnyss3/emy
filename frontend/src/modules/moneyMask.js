// Currency mask: a visible field shows "R$ 1.234,56" while a hidden field
// carries the plain decimal value the form submits. Driven by data attributes:
//   <input data-money-display data-money-target="id_target_amount">
//   <input type="hidden" id="id_target_amount" name="...">
export function initMoneyMask() {
    const displays = document.querySelectorAll("[data-money-display]");
    if (!displays.length) return;

    function format(cents) {
        return (
            "R$ " +
            (cents / 100).toLocaleString("pt-BR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            })
        );
    }

    displays.forEach((display) => {
        const hidden = document.getElementById(display.dataset.moneyTarget);
        if (!hidden) return;

        function sync() {
            const digits = (display.value || "").replace(/\D/g, "");
            const cents = digits ? parseInt(digits, 10) : 0;
            display.value = cents ? format(cents) : "";
            hidden.value = cents ? (cents / 100).toFixed(2) : "";
        }

        if (hidden.value) {
            const cents = Math.round(parseFloat(hidden.value) * 100);
            if (cents > 0) display.value = format(cents);
        }

        display.addEventListener("input", sync);
        display.addEventListener("blur", sync);
    });
}
