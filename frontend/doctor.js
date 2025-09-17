const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

let currentUser = null;
let authToken = null;

// Elementos de la interfaz
const userName = document.getElementById("userName");
const logoutBtn = document.getElementById("logoutBtn");
const authWarning = document.getElementById("authWarning");
const doctorApp = document.getElementById("doctorApp");

const textarea = document.getElementById("caseText");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");
const diffList = document.getElementById("diffList");
const testList = document.getElementById("testList");
const notes = document.getElementById("notes");

const loadPatientsBtn = document.getElementById("loadPatientsBtn");
const patientsList = document.getElementById("patientsList");
const patientsItems = document.getElementById("patientsItems");

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  statusEl.textContent = isLoading ? "Analizando..." : "";
}

function checkAuth() {
  const user = localStorage.getItem("user");
  const token = localStorage.getItem("token");
  if (!user || !token) {
    authWarning.classList.remove("hidden");
    doctorApp.classList.add("hidden");
    return false;
  }
  currentUser = JSON.parse(user);
  authToken = token;
  if (currentUser.user_type !== "doctor") {
    authWarning.classList.remove("hidden");
    doctorApp.classList.add("hidden");
    return false;
  }
  userName.textContent = `Dr. ${currentUser.full_name}`;
  authWarning.classList.add("hidden");
  doctorApp.classList.remove("hidden");
  return true;
}

async function apiCall(endpoint, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const resp = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (resp.status === 401) {
    window.location.href = "./login.html";
    throw new Error("No autorizado");
  }
  return resp;
}

function renderResults(data) {
  diffList.innerHTML = "";
  testList.innerHTML = "";
  notes.textContent = data.notes || "";
  (data.differentials || []).forEach((d) => {
    const li = document.createElement("li");
    const prob = d.probability ? ` (${d.probability})` : "";
    li.textContent = `${d.condition}${prob}: ${d.rationale}`;
    diffList.appendChild(li);
  });
  (data.tests || []).forEach((t) => {
    const li = document.createElement("li");
    li.textContent = `${t.name}${t.rationale ? ": " + t.rationale : ""}`;
    testList.appendChild(li);
  });
  results.classList.remove("hidden");
}

async function analyze() {
  const caseText = textarea.value.trim();
  if (caseText.length < 10) {
    alert("Ingresa un caso cl\u00ednico m\u00e1s detallado (m\u00ednimo 10 caracteres).");
    return;
  }
  setLoading(true);
  try {
    const resp = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_text: caseText }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `Solicitud fallida: ${resp.status}`);
    }
    const data = await resp.json();
    renderResults(data);
  } catch (e) {
    alert(e.message || "Error inesperado");
  } finally {
    setLoading(false);
  }
}

async function loadPatients() {
  try {
    const resp = await apiCall("/clinical-records/my-patients");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar la informaci\u00f3n");
    displayPatients(data.records);
  } catch (e) {
    alert(e.message);
  }
}

function displayPatients(records) {
  patientsItems.innerHTML = "";
  if (!records.length) {
    patientsItems.innerHTML = "<p>No se encontraron registros.</p>";
    patientsList.classList.remove("hidden");
    return;
  }
  records.forEach(r => {
    const div = document.createElement("div");
    div.className = "record-item";
    div.innerHTML = `
      <div class="record-header">
        <h4>${new Date(r.created_at).toLocaleString()}</h4>
        <span class="record-id">Paciente: ${r.patient_id}</span>
      </div>
      <p><strong>Caso:</strong> ${r.case_text}</p>
    `;
    patientsItems.appendChild(div);
  });
  patientsList.classList.remove("hidden");
}

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  window.location.href = "./login.html";
});

analyzeBtn.addEventListener("click", analyze);
loadPatientsBtn.addEventListener("click", loadPatients);

window.addEventListener("load", checkAuth);

