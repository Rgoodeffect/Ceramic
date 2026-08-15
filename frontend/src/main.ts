import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import "./style.css";

// Data fetching goes through api/client.ts's invoke() (a thin wrapper over
// frappe-ui's call()) against retail_suite's own whitelisted endpoints -
// frappe-ui's Resource/createResource system is not used here, so no
// further frappe-ui runtime configuration is needed.
const app = createApp(App);
app.use(createPinia());
app.mount("#ceramic-pos-app");
