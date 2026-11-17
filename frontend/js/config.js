/**
 * CareerLens — Global Application Configuration
 * ==============================================
 * Central configuration file for frontend client scripts.
 * Automatically resolves API_BASE for local development, local files, and cloud deployments.
 */

(function () {
  const isFile = window.location.protocol === "file:";
  // When running frontend on a separate dev server port (e.g. 8000 or 3000), target Flask port 5000:
  const isSeparateDevServer =
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") &&
    window.location.port !== "" &&
    window.location.port !== "5000";

  const apiBase = (isFile || isSeparateDevServer)
    ? "http://localhost:5000/api"
    : "/api";

  window.CAREERLENS_CONFIG = {
    API_BASE: apiBase,
    APP_NAME: "CareerLens",
    VERSION: "2.1.0",
  };
})();
