const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

let currentUser = null;
let authToken = null;

// UI elements
const userName = document.getElementById("userName");
const logoutBtn = document.getElementById("logoutBtn");
const authWarning = document.getElementById("authWarning");
const patientApp = document.getElementById("patientApp");

const loadHistoryBtn = document.getElementById("loadHistoryBtn");
const historyList = document.getElementById("historyList");
const historyItems = document.getElementById("historyItems");

const adjustFieldPath = document.getElementById("adjustFieldPath");
const adjustNewValue = document.getElementById("adjustNewValue");
const adjustReason = document.getElementById("adjustReason");
const submitAdjustmentBtn = document.getElementById("submitAdjustmentBtn");
const refreshAdjustmentsBtn = document.getElementById("refreshAdjustmentsBtn");
const patientAdjustments = document.getElementById("patientAdjustments");

const loadNotificationsBtn = document.getElementById("loadNotificationsBtn");
const notificationsList = document.getElementById("notificationsList");

const doctorEmail = document.getElementById("doctorEmail");
const shareRecordsBtn = document.getElementById("shareRecordsBtn");

const loadDoctorsBtn = document.getElementById("loadDoctorsBtn");
const doctorsList = document.getElementById("doctorsList");
const doctorsItems = document.getElementById("doctorsItems");

function checkAuth() {
  const user = localStorage.getItem("user");
  const token = localStorage.getItem("token");
  if (!user || !token) {
    authWarning.classList.remove("hidden");
    patientApp.classList.add("hidden");
    return false;
  }
  currentUser = JSON.parse(user);
  authToken = token;
  if (currentUser.user_type !== "patient") {
    authWarning.classList.remove("hidden");
    patientApp.classList.add("hidden");
    return false;
  }
  userName.textContent = currentUser.full_name;
  authWarning.classList.add("hidden");
  patientApp.classList.remove("hidden");
  return true;
}

async function apiCall(endpoint, options = {}) {
  const headers = { ...options.headers };
  if (options.body || (options.method && options.method !== "GET")) {
    headers["Content-Type"] = "application/json";
  }
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const resp = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (resp.status === 401) {
    window.location.href = "./login.html";
    throw new Error("Sesion caducada");
  }
  return resp;
}

async function loadHistory() {
  try {
    const resp = await apiCall("/clinical-records/my-history");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar la historia clinica");
    displayHistory(data.records || []);
  } catch (error) {
    alert(error.message);
  }
}

function displayHistory(records) {
  historyItems.innerHTML = "";
  if (!records.length) {
    historyItems.innerHTML = "<p>No se encontraron registros.</p>";
    historyList.classList.remove("hidden");
    return;
  }
  records.forEach((record) => {
    const div = document.createElement("div");
    div.className = "record-item";
    div.innerHTML = `
      <div class="record-header">
        <h4>${new Date(record.created_at).toLocaleString()}</h4>
        <span class="record-id">Doctor: ${record.doctor_id}</span>
      </div>
      <p><strong>Caso:</strong> ${record.case_text}</p>
    `;
    historyItems.appendChild(div);
  });
  historyList.classList.remove("hidden");
}

async function submitAdjustment() {
  const fieldPath = adjustFieldPath.value.trim();
  const newValue = adjustNewValue.value.trim();
  const reason = adjustReason.value.trim();

  if (!fieldPath || !newValue || reason.length < 3) {
    alert("Completa todos los campos y agrega una breve razon.");
    return;
  }

  try {
    const resp = await apiCall("/adjustments", {
      method: "POST",
      body: JSON.stringify({
        patient_id: currentUser.id,
        field_path: fieldPath,
        new_value: newValue,
        reason,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible registrar el ajuste");
    alert("Solicitud enviada correctamente");
    adjustFieldPath.value = "";
    adjustNewValue.value = "";
    adjustReason.value = "";
    await loadPatientAdjustments();
  } catch (error) {
    alert(error.message || "Error al enviar ajuste");
  }
}

async function loadPatientAdjustments() {
  try {
    const resp = await apiCall("/adjustments");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No se pudieron cargar los ajustes");
    renderPatientAdjustments(data.adjustments || []);
  } catch (error) {
    patientAdjustments.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

function renderPatientAdjustments(adjustments) {
  patientAdjustments.innerHTML = "";
  if (!adjustments.length) {
    patientAdjustments.innerHTML = "<p>No tienes solicitudes registradas.</p>";
    return;
  }
  adjustments.forEach((adj) => {
    const card = document.createElement("div");
    card.className = "card";
    const created = adj.created_at ? new Date(adj.created_at).toLocaleString() : "-";
    const decisionNote = adj.decision && adj.decision.rationale ? `<p><strong>Notas medicas:</strong> ${adj.decision.rationale}</p>` : "";
    card.innerHTML = `
      <h4>Campo: ${adj.field_path}</h4>
      <p><strong>Valor solicitado:</strong> ${adj.new_value}</p>
      <p><strong>Razon:</strong> ${adj.reason}</p>
      <p><strong>Estado actual:</strong> ${adj.status}</p>
      <p><strong>Creado:</strong> ${created}</p>
      ${decisionNote}
    `;
    patientAdjustments.appendChild(card);
  });
}

async function loadNotifications() {
  try {
    const resp = await apiCall("/notifications");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar las notificaciones");
    renderNotifications(data.notifications || []);
  } catch (error) {
    notificationsList.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

function renderNotifications(list) {
  notificationsList.innerHTML = "";
  if (!list.length) {
    notificationsList.innerHTML = "<p>No hay novedades.</p>";
    return;
  }
  list.forEach((item) => {
    const card = document.createElement("div");
    card.className = "card";
    const created = item.created_at ? new Date(item.created_at).toLocaleString() : "-";
    card.innerHTML = `
      <h4>${item.title || "Notificacion"}</h4>
      <p>${item.message}</p>
      <p><strong>Fecha:</strong> ${created}</p>
    `;
    notificationsList.appendChild(card);
  });
}

async function shareRecords() {
  const email = doctorEmail.value.trim();
  if (!email) {
    alert("Ingresa el correo del doctor");
    return;
  }
  try {
    const resp = await apiCall("/patients/share", {
      method: "POST",
      body: JSON.stringify({
        patient_id: currentUser.id,
        doctor_email: email,
        access_level: "read",
      }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible compartir los registros");
    alert(data.message);
    doctorEmail.value = "";
  } catch (error) {
    alert(error.message);
  }
}

async function loadDoctors() {
  try {
    const resp = await apiCall("/doctors");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar la lista de doctores");
    displayDoctors(data.doctors || []);
  } catch (error) {
    alert(error.message);
  }
}

function displayDoctors(list) {
  doctorsItems.innerHTML = "";
  if (!list.length) {
    doctorsItems.innerHTML = "<p>No se encontraron doctores.</p>";
    doctorsList.classList.remove("hidden");
    return;
  }
  list.forEach((doctor) => {
    const div = document.createElement("div");
    div.className = "doctor-item";
    div.innerHTML = `
      <div class="doctor-info">
        <h4>Dr. ${doctor.full_name}</h4>
        <p><strong>Especializacion:</strong> ${doctor.specialization || "No especificada"}</p>
        <p><strong>Licencia:</strong> ${doctor.license_number || "No proporcionada"}</p>
      </div>
    `;
    doctorsItems.appendChild(div);
  });
  doctorsList.classList.remove("hidden");
}

async function init() {
  if (!checkAuth()) return;
  await loadPatientAdjustments();
  await loadNotifications();
}

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  window.location.href = "./login.html";
});

loadHistoryBtn.addEventListener("click", loadHistory);
submitAdjustmentBtn.addEventListener("click", submitAdjustment);
refreshAdjustmentsBtn.addEventListener("click", loadPatientAdjustments);
loadNotificationsBtn.addEventListener("click", loadNotifications);
shareRecordsBtn.addEventListener("click", shareRecords);
loadDoctorsBtn.addEventListener("click", loadDoctors);

window.addEventListener("load", init);
