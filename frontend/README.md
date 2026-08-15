# Ceramic Showroom POS (frontend)

Vue 3 + TypeScript + Pinia + Frappe UI single-page app, embedded inside
ERPNext Desk as a Frappe Page (`retail_suite_core/page/ceramic_pos`) - not a
standalone application (see `CLAUDE.md` Part 2/4).

## Commands

```
npm install
npm run dev         # Vite dev server, proxies /api etc. to a local bench (see frappe-ui/vite frappeProxy)
npm run build        # outputs to ../retail_suite/public/frontend/ceramic_pos.js
npm run typecheck    # vue-tsc --noEmit
```

## How it's wired into Desk

`vite.config.ts` builds a single **IIFE** bundle (`ceramic_pos.js`, CSS
inlined) rather than Vite's default ES module output, because the Page
controller (`retail_suite_core/page/ceramic_pos/ceramic_pos.js`) loads it
with `frappe.require()`, which injects a plain `<script>` tag - a module
bundle's bare `import`/`export` syntax would fail there.

Every network call goes through `src/api/client.ts`'s `invoke()`, a thin
wrapper over `frappe-ui`'s `call()` that unwraps `retail_suite`'s uniform
`{success, message, data, errors}` response envelope (see
`retail_suite/api/utils.py`). No business logic lives in components or
stores - they only call whitelisted API endpoints and render results (spec
Part 6/10: "Client Script Policy").

## Known `npm run typecheck` noise

`frappe-ui` (pre-1.0) ships its own source (`.vue`/`.ts`, not a compiled
`dist` with declaration files) and its icon components resolve through a
Vite-only virtual module (`~icons/lucide/*`) provided by `unplugin-icons`.
Because of that, a plain `vue-tsc --noEmit` walks into `frappe-ui`'s own
internals via TypeScript's module resolution and reports errors there -
none of them are in this project's own code (verified: zero errors under
`src/`). This is a characteristic of consuming `frappe-ui` this way, not a
defect here. `npm run build` (Vite/esbuild, which does not type-check) is
the actual correctness gate for shipping, and it succeeds.

## Deployment

`bench build`/`bench install-app` do not automatically run this project's
own `npm run build` (that auto-detection convention varies across Frappe
versions and isn't something to depend on silently). Run it explicitly as
an install step - see `documentation/install-guide.md`.
