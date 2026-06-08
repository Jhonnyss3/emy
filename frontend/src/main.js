import { initPageLoader } from "./modules/pageLoader.js";
import { initScopeMenu } from "./modules/scopeMenu.js";
import { initPasswordToggle } from "./modules/passwordToggle.js";
import { initColorSwatches } from "./modules/colorSwatches.js";
import { initMoneyMask } from "./modules/moneyMask.js";
import { initCategoryDonut } from "./modules/categoryDonut.js";
import { initCategorySelect } from "./modules/categorySelect.js";
import { initFilterForm } from "./modules/filterForm.js";
import { initSelectWidget } from "./modules/selectWidget.js";
import { initForecastChart } from "./modules/forecastChart.js";
import { initDateWidget } from "./modules/dateWidget.js";
import { initLaunchModal } from "./modules/launchModal.js";

function init() {
    initPageLoader();
    initScopeMenu();
    initPasswordToggle();
    initColorSwatches();
    initMoneyMask();
    initCategoryDonut();
    initCategorySelect();
    initFilterForm();
    initSelectWidget();
    initForecastChart();
    initDateWidget();
    initLaunchModal();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
