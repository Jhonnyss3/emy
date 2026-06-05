import { defineConfig } from "vite";

// Vite builds only the JS bundle; TailwindCSS keeps running standalone.
// Output goes to frontend/dist and is wired into Django via django-vite,
// then picked up by collectstatic (STATICFILES_DIRS maps it to /static/dist/).
export default defineConfig({
    base: "/static/dist/",
    build: {
        manifest: "manifest.json",
        outDir: "frontend/dist",
        emptyOutDir: true,
        rollupOptions: {
            input: "frontend/src/main.js",
        },
    },
});
