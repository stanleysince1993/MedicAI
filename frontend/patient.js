const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

let currentUser = null;
let authToken = null;

// Elementos de la interfaz
const userName = document.getElementById("userName");
const logoutBtn = document.getElementById("logoutBtn");
const authWarning = document.getElementById("authWarning");
const patientApp = document.getElementById("patientApp");

const loadHistoryBtn = document.getElementById("loadHistoryBtn");
const historyList = document.getElementById("historyList");
const historyItems = document.getElementById("historyItems");

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
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const resp = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (resp.status === 401) {
    window.location.href = "./login.html";
    throw new Error("No autorizado");
  }
  return resp;
}

async function loadHistory() {
  try {
    const resp = await apiCall("/clinical-records/my-history");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar la historia cl\u00ednica");
    displayHistory(data.records);
  } catch (e) {
    alert(e.message);
  }
}

function displayHistory(records) {
  historyItems.innerHTML = "";
  if (!records.length) {
    historyItems.innerHTML = "<p>No se encontraron registros.</p>";
    historyList.classList.remove("hidden");
    return;
  }
  records.forEach(r => {
    const div = document.createElement("div");
    div.className = "record-item";
    div.innerHTML = `
      <div class="record-header">
        <h4>${new Date(r.created_at).toLocaleString()}</h4>
        <span class="record-id">Doctor: ${r.doctor_id}</span>
      </div>
      <p><strong>Caso:</strong> ${r.case_text}</p>
    `;
    historyItems.appendChild(div);
  });
  historyList.classList.remove("hidden");
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
        access_level: "read"
      })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible compartir los registros");
    alert(data.message);
    doctorEmail.value = "";
  } catch (e) {
    alert(e.message);
  }
}

async function loadDoctors() {
  try {
    const resp = await apiCall("/doctors");
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "No fue posible cargar la lista de doctores");
    displayDoctors(data.doctors);
  } catch (e) {
    alert(e.message);
  }
}

function displayDoctors(list) {
  doctorsItems.innerHTML = "";
  if (!list.length) {
    doctorsItems.innerHTML = "<p>No se encontraron doctores.</p>";
    doctorsList.classList.remove("hidden");
    return;
  }
  list.forEach(d => {
    const div = document.createElement("div");
    div.className = "doctor-item";
    div.innerHTML = `
      <div class="doctor-info">
        <h4>Dr. ${d.full_name}</h4>
        <p><strong>Especializaci\u00f3n:</strong> ${d.specialization || "No especificada"}</p>
        <p><strong>Licencia:</strong> ${d.license_number || "No proporcionada"}</p>
      </div>
    `;
    doctorsItems.appendChild(div);
  });
  doctorsList.classList.remove("hidden");
}

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  window.location.href = "./login.html";
});

loadHistoryBtn.addEventListener("click", loadHistory);
shareRecordsBtn.addEventListener("click", shareRecords);
loadDoctorsBtn.addEventListener("click", loadDoctors);

window.addEventListener("load", checkAuth);

