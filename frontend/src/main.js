import { initPageLoader } from "./modules/pageLoader.js";
import { initScopeMenu } from "./modules/scopeMenu.js";
import { initPasswordToggle } from "./modules/passwordToggle.js";
import { initColorSwatches } from "./modules/colorSwatches.js";
import { initMoneyMask } from "./modules/moneyMask.js";

function init() {
    initPageLoader();
    initScopeMenu();
    initPasswordToggle();
    initColorSwatches();
    initMoneyMask();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
