import { initPageLoader } from "./modules/pageLoader.js";
import { initScopeMenu } from "./modules/scopeMenu.js";
import { initPasswordToggle } from "./modules/passwordToggle.js";
import { initColorSwatches } from "./modules/colorSwatches.js";
import { initMoneyMask } from "./modules/moneyMask.js";
import { initCategoryDonut } from "./modules/categoryDonut.js";

function init() {
    initPageLoader();
    initScopeMenu();
    initPasswordToggle();
    initColorSwatches();
    initMoneyMask();
    initCategoryDonut();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
