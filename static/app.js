// Browser interactions for fetching and pushing Walmart freight loads.

const constants = JSON.parse(document.querySelector("#app-config").textContent);
const fetchButton = document.querySelector("#fetch-button");
const pushButton = document.querySelector("#push-button");
const statusElement = document.querySelector("#status");
const loadsBody = document.querySelector("#loads-body");
const feedback = document.querySelector("#feedback");
const feedbackSummary = document.querySelector("#feedback-summary");
const feedbackResults = document.querySelector("#feedback-results");
let loads = [];

function setBusy(isBusy) {
  fetchButton.disabled = isBusy;
  pushButton.disabled = isBusy || loads.length === 0;
}

function setStatus(message, state) {
  statusElement.textContent = message;
  statusElement.dataset.state = state;
}

function updateSummary({ fetched = 0, sanitized = 0, pushed = 0, rejected = 0 }) {
  document.querySelector("#fetched-count").textContent = fetched;
  document.querySelector("#sanitized-count").textContent = sanitized;
  document.querySelector("#pushed-count").textContent = pushed;
  document.querySelector("#rejected-count").textContent = rejected;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderLoads() {
  if (loads.length === 0) {
    loadsBody.innerHTML = `<tr><td colspan="11" class="empty">${constants.ui.no_loads}</td></tr>`;
    return;
  }

  loadsBody.innerHTML = loads.map((load) => `
    <tr>
      <td>${escapeHtml(load.load_no)}</td>
      <td>${escapeHtml(load.frt_ord_no)}</td>
      <td>${escapeHtml(load.shipper_nm)}</td>
      <td>${escapeHtml(load.orig_city)}</td>
      <td>${escapeHtml(load.orig_st)}</td>
      <td>${escapeHtml(load.dest_city)}</td>
      <td>${escapeHtml(load.dest_st)}</td>
      <td>${escapeHtml(load.shp_dt)}</td>
      <td>${escapeHtml(load.del_dt)}</td>
      <td>${escapeHtml(load.wgt)}</td>
      <td>${escapeHtml(load.mode)}</td>
    </tr>
  `).join("");
}

async function fetchLoads() {
  setBusy(true);
  setStatus(constants.ui.status_loading, "loading");
  feedback.hidden = true;

  try {
    const response = await fetch("/api/walmart/loads");
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || constants.ui.status_error);
    loads = data.loads || [];
    updateSummary({ fetched: loads.length });
    renderLoads();
    setStatus(constants.ui.status_success, "success");
  } catch (error) {
    loads = [];
    renderLoads();
    setStatus(`${constants.ui.error_prefix} ${error.message}`, "error");
  } finally {
    setBusy(false);
  }
}

// Renders one card per load using the server's per-load `results` array (status/payload/errors).
function renderResultCard(result) {
  const isPushed = result.status === "pushed";
  const cardClass = isPushed ? "result-card--pushed" : "result-card--rejected";
  const badgeClass = isPushed ? "result-badge--pushed" : "result-badge--rejected";
  const badgeLabel = isPushed ? constants.ui.pushed_label : constants.ui.rejected_label;
  const errors = result.errors && result.errors.length
    ? `<ul class="result-errors">${result.errors.map((message) => `<li>${escapeHtml(message)}</li>`).join("")}</ul>`
    : "";

  return `
    <article class="result-card ${cardClass}">
      <div class="result-card-heading">
        <span class="result-badge ${badgeClass}">${escapeHtml(badgeLabel)}</span>
        <strong>${escapeHtml(result.load_number)}</strong>
      </div>
      <p class="result-sent-label">${escapeHtml(constants.ui.sent_label)}</p>
      <pre class="result-payload">${escapeHtml(JSON.stringify(result.payload, null, 2))}</pre>
      ${errors}
    </article>
  `;
}

function renderPushResults(data) {
  const results = data.results || [];
  if (results.length === 0) {
    feedbackSummary.textContent = "";
    feedbackResults.innerHTML = `<p class="result-message">${escapeHtml(data.message || constants.ui.status_error)}</p>`;
    return { accepted: 0, total: 0 };
  }

  const accepted = results.filter((result) => result.status === "pushed").length;
  feedbackSummary.textContent = `${accepted}/${results.length} ${constants.ui.results_accepted_suffix}`;
  feedbackResults.innerHTML = results.map(renderResultCard).join("");
  return { accepted, total: results.length };
}

async function pushLoads() {
  setBusy(true);
  setStatus(constants.ui.status_loading, "loading");
  feedback.hidden = true;

  try {
    const response = await fetch("/api/shv/loads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ loads }),
    });
    const data = await response.json();
    const { accepted, total } = renderPushResults(data);
    updateSummary({ fetched: loads.length, sanitized: loads.length, pushed: accepted, rejected: total - accepted });
    feedback.hidden = false;
    if (!response.ok) throw new Error(data.message || constants.ui.status_error);
    setStatus(constants.ui.status_success, "success");
  } catch (error) {
    setStatus(`${constants.ui.error_prefix} ${error.message}`, "error");
  } finally {
    setBusy(false);
  }
}

fetchButton.addEventListener("click", fetchLoads);
pushButton.addEventListener("click", pushLoads);