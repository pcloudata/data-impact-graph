const datasetEl = document.getElementById("dataset");
const runEl = document.getElementById("run");
const outputEl = document.getElementById("output");
const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const ownerEl = document.getElementById("owner");
const p1El = document.getElementById("p1");
const ticketsEl = document.getElementById("tickets");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

async function loadDatasets() {
  setStatus("Loading datasets…");
  runEl.disabled = true;
  const response = await fetch("/datasets");
  if (!response.ok) {
    throw new Error(`Failed to load datasets (${response.status})`);
  }
  const payload = await response.json();
  datasetEl.innerHTML = "";
  for (const row of payload.datasets) {
    const option = document.createElement("option");
    option.value = row.id;
    option.textContent = row.id;
    datasetEl.appendChild(option);
  }
  const preferred = "acme.raw.sales.orders";
  if ([...datasetEl.options].some((opt) => opt.value === preferred)) {
    datasetEl.value = preferred;
  }
  runEl.disabled = false;
  setStatus(`${payload.datasets.length} datasets loaded`);
}

async function runImpact() {
  const dataset = datasetEl.value;
  if (!dataset) return;
  setStatus(`Querying impact for ${dataset}…`);
  runEl.disabled = true;
  try {
    const response = await fetch(`/impact?dataset=${encodeURIComponent(dataset)}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || `Request failed (${response.status})`);
    }
    outputEl.textContent = JSON.stringify(payload, null, 2);
    ownerEl.textContent = payload.owner_team || "(unowned)";
    const p1 = (payload.reports || [])
      .filter((r) => r.criticality === "P1")
      .map((r) => r.name);
    p1El.textContent = p1.length ? p1.join(", ") : "None";
    const tickets = (payload.open_tickets || []).map((t) => t.id);
    ticketsEl.textContent = tickets.length ? tickets.join(", ") : "None";
    summaryEl.hidden = false;
    setStatus("Impact ready");
  } catch (err) {
    summaryEl.hidden = true;
    outputEl.textContent = String(err.message || err);
    setStatus(String(err.message || err), true);
  } finally {
    runEl.disabled = false;
  }
}

runEl.addEventListener("click", runImpact);
datasetEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") runImpact();
});

loadDatasets().catch((err) => {
  setStatus(String(err.message || err), true);
  outputEl.textContent = String(err.message || err);
});
