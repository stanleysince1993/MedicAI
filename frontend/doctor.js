const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

let currentUser = null;
let authToken = null;
let selectedIcdCodes = [];
let lastDashboardPatientId = null;

// UI Elements
const userName = document.getElementById("userName");
const logoutBtn = document.getElementById("logoutBtn");
const authWarning = document.getElementById("authWarning");
const doctorApp = document.getElementById("doctorApp");

const textarea = document.getElementById("caseText");
const analyzeBtn = document.getElementById("analyzeBtn");
const suggestIcdBtn = document.getElementById("suggestIcdBtn");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");
const diffList = document.getElementById("diffList");
const testList = document.getElementById("testList");
const notes = document.getElementById("notes");
const icdSuggestions = document.getElementById("icdSuggestions");
const icdResults = document.getElementById("icdResults");
const icdAccepted = document.getElementById("icdAccepted");

const loadPatientsBtn = document.getElementById("loadPatientsBtn");
const patientsList = document.getElementById("patientsList");
const patientsItems = document.getElementById("patientsItems");

const loadAdjustmentsBtn = document.getElementById("loadAdjustmentsBtn");
const adjustmentsContainer = document.getElementById("adjustmentsContainer");

const dashboardPatientIdInput = document.getElementById("dashboardPatientId");
const loadDashboardBtn = document.getElementById("loadDashboardBtn");
const dashboardSummary = document.getElementById("dashboardSummary");
const activeAlertsCount = document.getElementById("activeAlertsCount");
const alertsList = document.getElementById("alertsList");

const calculatorSelect = document.getElementById("calculatorSelect");
const calculatorForm = document.getElementById("calculatorForm");
const calculatorInputs = document.getElementById("calculatorInputs");
const calculatorResult = document.getElementById("calculatorResult");

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  suggestIcdBtn.disabled = isLoading;
  statusEl.textContent = isLoading ? "Procesando..." : "";
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
  const headers = { ...options.headers };
  if (!(options && options.body) && !options.method) {
    // default GET
  } else {
    headers["Content-Type"] = "application/json";
  }
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (response.status === 401) {
    window.location.href = "./login.html";
    throw new Error("Sesión no válida");
  }
  return response;
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
    alert("Ingresa un caso clínico más detallado (mínimo 10 caracteres).");
    return;
  }
  setLoading(true);
  try {
    const resp = await apiCall("/analyze", {
      method: "POST",
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

async function suggestIcd() {
  const caseText = textarea.value.trim();
  if (caseText.length < 10) {
    alert("Proporciona un caso clínico más amplio para sugerir códigos.");
    return;
  }
  setLoading(true);
  try {
    const resp = await apiCall("/icd10/suggest", {
      method: "POST",
      body: JSON.stringify({ text: caseText }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "No fue posible obtener sugerencias");
    }
    const data = await resp.json();
    renderIcdSuggestions(data.codes || []);
  } catch (error) {
    alert(error.message || "Error al generar sugerencias");
  } finally {
    setLoading(false);
  }
}

function renderIcdSuggestions(suggestions) {
  icdResults.innerHTML = "";
  if (!suggestions.length) {
    icdSuggestions.classList.add("hidden");
    alert("No se encontraron sugerencias relevantes.");
    return;
  }
  icdSuggestions.classList.remove("hidden");

  suggestions.forEach((item) => {
    const li = document.createElement("li");
    li.className = "icd-item";
    const badge = item.needsReview ? "<span class=\"badge warning\">Revisar</span>" : "";
    li.innerHTML = `
      <div>
        <strong>${item.code}</strong> - ${item.label} (confianza: ${(item.confidence * 100).toFixed(0)}%) ${badge}
      </div>
    `;
    const btnGroup = document.createElement("div");
    btnGroup.className = "actions gap";

    const acceptBtn = document.createElement("button");
    acceptBtn.textContent = "Aceptar";
    acceptBtn.className = "btn-small";
    acceptBtn.onclick = () => acceptIcdSuggestion(item);

    const rejectBtn = document.createElement("button");
    rejectBtn.textContent = "Rechazar";
    rejectBtn.className = "btn-small secondary";
    rejectBtn.onclick = () => li.remove();

    btnGroup.appendChild(acceptBtn);
    btnGroup.appendChild(rejectBtn);
    li.appendChild(btnGroup);

    icdResults.appendChild(li);
  });
}

function acceptIcdSuggestion(item) {
  if (selectedIcdCodes.find((x) => x.code === item.code)) {
    alert("Este código ya fue agregado.");
    return;
  }
  selectedIcdCodes.push(item);
  renderAcceptedIcd();
}

function renderAcceptedIcd() {
  icdAccepted.innerHTML = "";
  if (!selectedIcdCodes.length) {
    icdAccepted.innerHTML = "<li>No hay códigos seleccionados.</li>";
    return;
  }
  selectedIcdCodes.forEach((item, index) => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${item.code}</strong> - ${item.label}`;
    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Quitar";
    removeBtn.className = "btn-small secondary";
    removeBtn.onclick = () => {
      selectedIcdCodes.splice(index, 1);
      renderAcceptedIcd();
    };
    li.appendChild(removeBtn);
    icdAccepted.appendChild(li);
  });
}

async function loadPatients() {
  try {
    const resp = await apiCall("/clinical-records/my-patients");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar la información");
    displayPatients(data.records || []);
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
  records.forEach((record) => {
    const div = document.createElement("div");
    div.className = "record-item";
    div.innerHTML = `
      <div class="record-header">
        <h4>${new Date(record.created_at).toLocaleString()}</h4>
        <span class="record-id">Paciente: ${record.patient_id}</span>
      </div>
      <p><strong>Caso:</strong> ${record.case_text}</p>
    `;
    patientsItems.appendChild(div);
  });
  patientsList.classList.remove("hidden");
}

async function loadAdjustments() {
  try {
    const resp = await apiCall("/adjustments");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar ajustes");
    renderAdjustments(data.adjustments || []);
  } catch (error) {
    adjustmentsContainer.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

function renderAdjustments(adjustments) {
  adjustmentsContainer.innerHTML = "";
  if (!adjustments.length) {
    adjustmentsContainer.innerHTML = "<p>No hay solicitudes pendientes.</p>";
    return;
  }
  adjustments.forEach((adj) => {
    const card = document.createElement("div");
    card.className = "card";
    const created = adj.created_at ? new Date(adj.created_at).toLocaleString() : "-";
    card.innerHTML = `
      <h4>Paciente: ${adj.patient_id}</h4>
      <p><strong>Campo:</strong> ${adj.field_path}</p>
      <p><strong>Nuevo valor:</strong> ${adj.new_value}</p>
      <p><strong>Razón:</strong> ${adj.reason}</p>
      <p><strong>Estado:</strong> ${adj.status}</p>
      <p><strong>Solicitado:</strong> ${created}</p>
    `;

    if (Array.isArray(adj.audit_trail) && adj.audit_trail.length) {
      const timeline = document.createElement("ul");
      timeline.className = "timeline";
      adj.audit_trail.forEach((entry) => {
        const li = document.createElement("li");
        const ts = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : "-";
        li.textContent = `${entry.action} por ${entry.actor_role} (${ts})`;
        timeline.appendChild(li);
      });
      card.appendChild(timeline);
    }

    if (adj.status === "requested" || adj.status === "under-review") {
      const actions = document.createElement("div");
      actions.className = "actions gap";

      const approveBtn = document.createElement("button");
      approveBtn.textContent = "Aprobar";
      approveBtn.className = "btn-small";
      approveBtn.onclick = () => decideAdjustment(adj.id, "approved");

      const rejectBtn = document.createElement("button");
      rejectBtn.textContent = "Rechazar";
      rejectBtn.className = "btn-small secondary";
      rejectBtn.onclick = () => decideAdjustment(adj.id, "rejected");

      actions.appendChild(approveBtn);
      actions.appendChild(rejectBtn);
      card.appendChild(actions);
    }

    adjustmentsContainer.appendChild(card);
  });
}

async function decideAdjustment(id, status) {
  const rationale = prompt("Notas para la decisión (opcional):") || "";
  try {
    const resp = await apiCall(`/adjustments/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ status, rationale }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible actualizar el ajuste");
    alert(`Solicitud ${status === "approved" ? "aprobada" : "rechazada"}`);
    loadAdjustments();
  } catch (error) {
    alert(error.message || "Error al registrar la decisión");
  }
}

async function loadDashboard(patientId) {
  try {
    const resp = await apiCall(`/dashboard/${patientId}`);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible obtener el dashboard");
    lastDashboardPatientId = patientId;
    renderDashboard(data);
  } catch (error) {
    alert(error.message || "Error al cargar dashboard");
  }
}

function renderDashboard(data) {
  activeAlertsCount.textContent = data.activeAlerts ?? 0;
  alertsList.innerHTML = "";
  dashboardSummary.classList.remove("hidden");

  const alerts = data.alerts || [];
  if (!alerts.length) {
    alertsList.innerHTML = "<p>No hay alertas registradas.</p>";
    return;
  }

  alerts.forEach((alert) => {
    const div = document.createElement("div");
    div.className = `card alert-${alert.severity}`;
    const observed = alert.observedAt ? new Date(alert.observedAt).toLocaleString() : "-";
    div.innerHTML = `
      <h4>${alert.code} • severidad ${alert.severity}</h4>
      <p><strong>Estado:</strong> ${alert.status}</p>
      <p><strong>Observado:</strong> ${observed}</p>
      <p>${alert.message || ""}</p>
    `;

    const actionButton = document.createElement("button");
    actionButton.className = "btn-small";
    if (alert.status === "open") {
      actionButton.textContent = "Reconocer";
      actionButton.onclick = () => updateAlertStatus(alert.id, "acknowledged");
      div.appendChild(actionButton);
    } else if (alert.status === "acknowledged") {
      actionButton.textContent = "Resolver";
      actionButton.onclick = () => updateAlertStatus(alert.id, "resolved");
      div.appendChild(actionButton);
    } else if (alert.status === "resolved") {
      actionButton.textContent = "Cerrar";
      actionButton.onclick = () => updateAlertStatus(alert.id, "closed");
      div.appendChild(actionButton);
    }
    alertsList.appendChild(div);
  });
}

async function updateAlertStatus(alertId, status) {
  const notes = prompt("Notas para la acción (opcional):") || "";
  try {
    const resp = await apiCall(`/alerts/${alertId}/status`, {
      method: "POST",
      body: JSON.stringify({ status, notes }),
    });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      throw new Error(data.detail || "No fue posible actualizar la alerta");
    }
    if (lastDashboardPatientId) {
      loadDashboard(lastDashboardPatientId);
    }
  } catch (error) {
    alert(error.message || "Error al actualizar alerta");
  }
}

const calculatorSchemas = {
  "bmi": [
    { id: "weight_kg", label: "Peso (kg)", type: "number", step: "0.1", required: true },
    { id: "height_cm", label: "Estatura (cm)", type: "number", step: "0.1", required: true },
  ],
  "egfr": [
    { id: "creatinine_mg_dl", label: "Creatinina (mg/dL)", type: "number", step: "0.1", required: true },
    { id: "age", label: "Edad", type: "number", required: true },
    { id: "sex", label: "Sexo", type: "select", options: [
      { value: "male", label: "Masculino" },
      { value: "female", label: "Femenino" },
    ], required: true },
    { id: "race", label: "Raza", type: "select", options: [
      { value: "", label: "Seleccionar" },
      { value: "black", label: "Afrodescendiente" },
      { value: "other", label: "Otra" },
    ] },
  ],
  "cha2ds2-vasc": [
    { id: "age", label: "Edad", type: "number", required: true },
    { id: "sex", label: "Sexo", type: "select", options: [
      { value: "male", label: "Masculino" },
      { value: "female", label: "Femenino" },
    ], required: true },
    { id: "congestive_heart_failure", label: "Falla cardiaca", type: "checkbox" },
    { id: "hypertension", label: "Hipertensión", type: "checkbox" },
    { id: "diabetes", label: "Diabetes", type: "checkbox" },
    { id: "stroke_tia", label: "Evento cerebrovascular previo", type: "checkbox" },
    { id: "vascular_disease", label: "Enfermedad vascular", type: "checkbox" },
  ],
  "curb-65": [
    { id: "confusion", label: "Confusión", type: "checkbox" },
    { id: "urea_mmol_l", label: "Urea (mmol/L)", type: "number", step: "0.1", required: true },
    { id: "respiratory_rate", label: "Frecuencia respiratoria", type: "number", required: true },
    { id: "systolic_bp", label: "PA sistólica", type: "number", required: true },
    { id: "diastolic_bp", label: "PA diastólica", type: "number", required: true },
    { id: "age", label: "Edad", type: "number", required: true },
  ],
};

function renderCalculatorInputs(tool) {
  const schema = calculatorSchemas[tool];
  calculatorInputs.innerHTML = "";
  schema.forEach((field) => {
    const wrapper = document.createElement("label");
    wrapper.className = "input-item";
    wrapper.setAttribute("for", field.id);
    wrapper.textContent = field.label;

    let input;
    if (field.type === "select") {
      input = document.createElement("select");
      field.options.forEach((option) => {
        const opt = document.createElement("option");
        opt.value = option.value;
        opt.textContent = option.label;
        input.appendChild(opt);
      });
    } else if (field.type === "checkbox") {
      input = document.createElement("input");
      input.type = "checkbox";
    } else {
      input = document.createElement("input");
      input.type = field.type;
      if (field.step) input.step = field.step;
    }
    input.id = field.id;
    input.name = field.id;
    if (field.required) input.required = true;
    wrapper.appendChild(input);
    calculatorInputs.appendChild(wrapper);
  });
}

function collectCalculatorInputs(tool) {
  const schema = calculatorSchemas[tool];
  const payload = {};
  for (const field of schema) {
    const el = document.getElementById(field.id);
    if (!el) continue;
    if (field.type === "checkbox") {
      payload[field.id] = el.checked;
    } else if (field.type === "number") {
      const value = parseFloat(el.value);
      if (Number.isNaN(value)) {
        throw new Error(`Dato inválido para ${field.label}`);
      }
      payload[field.id] = value;
    } else {
      payload[field.id] = el.value;
    }
  }
  return payload;
}

async function submitCalculator(event) {
  event.preventDefault();
  const tool = calculatorSelect.value;
  try {
    const payload = collectCalculatorInputs(tool);
    const params = new URLSearchParams({
      tool,
      inputs: JSON.stringify(payload),
    });
    const resp = await apiCall(`/calculate?${params.toString()}`);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible calcular");
    renderCalculatorResult(data);
  } catch (error) {
    alert(error.message || "Error en calculadora");
  }
}

function renderCalculatorResult(result) {
  calculatorResult.innerHTML = `
    <p><strong>Resultado:</strong> ${result.value} ${result.units || ""}</p>
    <p><strong>Severidad:</strong> ${(result.flags || []).join(", ") || "sin banderas"}</p>
  `;
  calculatorResult.classList.remove("hidden");
}

async function init() {
  if (!checkAuth()) return;

  renderCalculatorInputs(calculatorSelect.value);
  renderAcceptedIcd();
  await loadAdjustments();
}

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  window.location.href = "./login.html";
});

analyzeBtn.addEventListener("click", analyze);
suggestIcdBtn.addEventListener("click", suggestIcd);
loadPatientsBtn.addEventListener("click", loadPatients);
loadAdjustmentsBtn.addEventListener("click", loadAdjustments);
loadDashboardBtn.addEventListener("click", () => {
  const patientId = dashboardPatientIdInput.value.trim();
  if (!patientId) {
    alert("Introduce un ID de paciente");
    return;
  }
  loadDashboard(patientId);
});

calculatorSelect.addEventListener("change", () => {
  renderCalculatorInputs(calculatorSelect.value);
  calculatorResult.classList.add("hidden");
});

calculatorForm.addEventListener("submit", submitCalculator);

window.addEventListener("load", init);
