/**
 * CareerLens — api.js
 * ====================
 * Drop this in frontend/js/
 * All fetch() calls to the Flask backend live here.
 *
 * Uses centralized window.CAREERLENS_CONFIG.API_BASE with fallback.
 */

const CareerAPI = (() => {
  const getBaseUrl = () => {
    if (window.CAREERLENS_CONFIG && window.CAREERLENS_CONFIG.API_BASE) {
      return window.CAREERLENS_CONFIG.API_BASE;
    }
    const isFile = window.location.protocol === "file:";
    const isSeparateDevServer =
      (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") &&
      window.location.port !== "" &&
      window.location.port !== "5000";
    return (isFile || isSeparateDevServer) ? "http://localhost:5000/api" : "/api";
  };

  async function _post(path, body) {
    const res = await fetch(`${getBaseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  async function _get(path) {
    const res = await fetch(`${getBaseUrl()}${path}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  /**
   * Submit assessment answers.
   * @param {Object} answers — { "Q1": 4, "Q2": 5, ... }
   * @returns {Promise<Object>} — { skill_profile, top5, skill_gaps, roadmaps }
   */
  async function submitAnswers(answers) {
    const userId = sessionStorage.getItem("cl_user_id");
    if (!userId) throw new Error("Not logged in. Please register or log in first.");
    return _post("/submit", { user_id: Number(userId), answers });
  }

  /**
   * Save in-progress assessment draft responses.
   * @param {Object} answers — { "Q1": 4, "Q2": 5, ... }
   */
  async function saveDraft(answers) {
    const userId = sessionStorage.getItem("cl_user_id") || localStorage.getItem("cl_user_id");
    if (!userId) return null;
    return _post("/assessment/draft", { user_id: Number(userId), answers });
  }

  /**
   * Fetch active draft responses for a user.
   */
  async function getDraft(userId) {
    const uid = userId || sessionStorage.getItem("cl_user_id") || localStorage.getItem("cl_user_id");
    if (!uid) return { draft: null, has_draft: false };
    return _get(`/assessment/draft/${uid}`);
  }

  /**
   * Fetch the latest saved results for the current user.
   */
  async function getResults(userId) {
    const uid = userId || sessionStorage.getItem("cl_user_id");
    if (!uid) throw new Error("No user_id available.");
    return _get(`/results/${uid}`);
  }

  /**
   * Fetch all assessment attempts / history for a user.
   */
  async function getUserHistory(userId) {
    const uid = userId || sessionStorage.getItem("cl_user_id");
    if (!uid) throw new Error("No user_id available.");
    return _get(`/user/${uid}/history`);
  }

  /**
   * Fetch results for a specific assessment attempt by assessment_id.
   */
  async function getAssessmentResults(assessmentId) {
    if (!assessmentId) throw new Error("No assessment_id provided.");
    return _get(`/assessment/${assessmentId}/results`);
  }

  /**
   * Fetch all careers catalog.
   */
  async function getCareers() {
    return _get("/careers");
  }

  return { submitAnswers, saveDraft, getDraft, getResults, getUserHistory, getAssessmentResults, getCareers };
})();
