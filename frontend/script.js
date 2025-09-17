const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

// Authentication
let currentUser = null;
let authToken = null;

// UI elements
const textarea = document.getElementById("caseText");
const button = document.getElementById("analyzeBtn");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");
const diffList = document.getElementById("diffList");
const testList = document.getElementById("testList");
const notes = document.getElementById("notes");

// Auth elements
const loginPrompt = document.getElementById("loginPrompt");
const appContent = document.getElementById("appContent");
const userName = document.getElementById("userName");
const logoutBtn = document.getElementById("logoutBtn");

// History elements
const loadHistoryBtn = document.getElementById("loadHistoryBtn");
const historyList = document.getElementById("historyList");
const historyItems = document.getElementById("historyItems");

// Doctor elements
const doctorFeatures = document.getElementById("doctorFeatures");
const loadPatientsBtn = document.getElementById("loadPatientsBtn");
const patientsList = document.getElementById("patientsList");
const patientsItems = document.getElementById("patientsItems");
const createRecordBtn = document.getElementById("createRecordBtn");

// Patient elements
const patientFeatures = document.getElementById("patientFeatures");
const doctorEmail = document.getElementById("doctorEmail");
const shareRecordsBtn = document.getElementById("shareRecordsBtn");
const loadDoctorsBtn = document.getElementById("loadDoctorsBtn");
const doctorsList = document.getElementById("doctorsList");
const doctorsItems = document.getElementById("doctorsItems");

function setLoading(isLoading) {
  button.disabled = isLoading;
  statusEl.textContent = isLoading ? "Analizando..." : "";
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
    alert("Ingresa un caso cl\\u00ednico m\\u00e1s detallado (m\\u00ednimo 10 caracteres).");
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

// Terminal code removed

// Authentication functions
function checkAuth() {
  const user = localStorage.getItem("user");
  const token = localStorage.getItem("token");
  
  if (user && token) {
    currentUser = JSON.parse(user);
    authToken = token;
    showApp();
  } else {
    showLoginPrompt();
  }
}

function showLoginPrompt() {
  loginPrompt.classList.remove("hidden");
  appContent.classList.add("hidden");
}

function showApp() {
  loginPrompt.classList.add("hidden");
  appContent.classList.remove("hidden");
  
  const roleLabel = currentUser.user_type === "doctor" ? "Doctor" : "Paciente";
  userName.textContent = `Bienvenido(a), ${currentUser.full_name} (${roleLabel})`;
  
  // Mostrar funciones segun el tipo de usuario
  if (currentUser.user_type === "doctor") {
    doctorFeatures.classList.remove("hidden");
    patientFeatures.classList.add("hidden");
  } else {
    doctorFeatures.classList.add("hidden");
    patientFeatures.classList.remove("hidden");
  }
}

function logout() {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  currentUser = null;
  authToken = null;
  showLoginPrompt();
}

// API helper with authentication
async function apiCall(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers
  };
  
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });
  
  if (response.status === 401) {
    logout();
    throw new Error("La sesi\u00f3n expir\u00f3. Inicia sesi\u00f3n nuevamente.");
  }
  
  return response;
}

// Clinical history functions
async function loadHistory() {
  try {
    const response = await apiCall("/clinical-records/my-history");
    const data = await response.json();
    
    if (response.ok) {
      displayHistory(data.records);
    } else {
      alert(data.detail || "No fue posible cargar la historia");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

function displayHistory(records) {
  historyItems.innerHTML = "";
  
  if (records.length === 0) {
    historyItems.innerHTML = "<p>No se encontraron registros cl\u00ednicos.</p>";
    return;
  }
  
  records.forEach(record => {
    const recordDiv = document.createElement("div");
    recordDiv.className = "record-item";
    recordDiv.innerHTML = `
      <div class="record-header">
        <h4>Registro del ${new Date(record.created_at).toLocaleDateString()}</h4>
        <span class="record-id">ID: ${record.id}</span>
      </div>
      <div class="record-content">
        <p><strong>Caso:</strong> ${record.case_text}</p>
        <div class="record-details">
          <div class="differentials">
            <strong>Diferenciales:</strong>
            <ul>
              ${record.differentials.map(d => `<li>${d.condition}: ${d.rationale}</li>`).join("")}
            </ul>
          </div>
          <div class="tests">
            <strong>Pruebas:</strong>
            <ul>
              ${record.tests.map(t => `<li>${t.name}: ${t.rationale || ""}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `;
    historyItems.appendChild(recordDiv);
  });
  
  historyList.classList.remove("hidden");
}

// Doctor functions
async function loadPatients() {
  try {
    const response = await apiCall("/clinical-records/my-patients");
    const data = await response.json();
    
    if (response.ok) {
      displayPatients(data.records);
    } else {
      alert(data.detail || "No fue posible cargar los registros de pacientes");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

function displayPatients(records) {
  patientsItems.innerHTML = "";
  
  if (records.length === 0) {
    patientsItems.innerHTML = "<p>No se encontraron registros de pacientes.</p>";
    return;
  }
  
  records.forEach(record => {
    const recordDiv = document.createElement("div");
    recordDiv.className = "record-item";
    recordDiv.innerHTML = `
      <div class="record-header">
        <h4>Registro del ${new Date(record.created_at).toLocaleDateString()}</h4>
        <span class="record-id">ID de paciente: ${record.patient_id}</span>
      </div>
      <div class="record-content">
        <p><strong>Caso:</strong> ${record.case_text}</p>
        <div class="record-details">
          <div class="differentials">
            <strong>Diferenciales:</strong>
            <ul>
              ${record.differentials.map(d => `<li>${d.condition}: ${d.rationale}</li>`).join("")}
            </ul>
          </div>
          <div class="tests">
            <strong>Pruebas:</strong>
            <ul>
              ${record.tests.map(t => `<li>${t.name}: ${t.rationale || ""}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `;
    patientsItems.appendChild(recordDiv);
  });
  
  patientsList.classList.remove("hidden");
}

// Patient functions
async function shareRecords() {
  const email = doctorEmail.value.trim();
  if (!email) {
    alert("Ingresa el correo del doctor");
    return;
  }
  
  try {
    const response = await apiCall("/patients/share", {
      method: "POST",
      body: JSON.stringify({
        patient_id: currentUser.id,
        doctor_email: email,
        access_level: "read"
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      alert(data.message);
      doctorEmail.value = "";
    } else {
      alert(data.detail || "No fue posible compartir los registros");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

async function loadDoctors() {
  try {
    const response = await apiCall("/doctors");
    const data = await response.json();
    
    if (response.ok) {
      displayDoctors(data.doctors);
    } else {
      alert(data.detail || "No fue posible cargar la lista de doctores");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

function displayDoctors(doctors) {
  doctorsItems.innerHTML = "";
  
  if (doctors.length === 0) {
    doctorsItems.innerHTML = "<p>No se encontraron doctores.</p>";
    return;
  }
  
  doctors.forEach(doctor => {
    const doctorDiv = document.createElement("div");
    doctorDiv.className = "doctor-item";
    doctorDiv.innerHTML = `
      <div class="doctor-info">
        <h4>Dr. ${doctor.full_name}</h4>
        <p><strong>Especialidad:</strong> ${doctor.specialization || "No especificada"}</p>
        <p><strong>Licencia:</strong> ${doctor.license_number || "No proporcionada"}</p>
        <button onclick="shareWithDoctor('${doctor.id}', '${doctor.full_name}')" class="btn-small">
          Compartir registros
        </button>
      </div>
    `;
    doctorsItems.appendChild(doctorDiv);
  });
  
  doctorsList.classList.remove("hidden");
}

function shareWithDoctor(doctorId, doctorName) {
  if (confirm(`Compartir tus registros con el Dr. ${doctorName}?`)) {
    // This would need the doctor's email, but for demo we'll use a placeholder
    alert("Utiliza el campo de correo superior para compartir con este doctor.");
  }
}

// Event listeners
button.addEventListener("click", analyze);
logoutBtn.addEventListener("click", logout);
loadHistoryBtn.addEventListener("click", loadHistory);
loadPatientsBtn.addEventListener("click", loadPatients);
createRecordBtn.addEventListener("click", function() {
  window.location.href = './patient-registration.html';
});
shareRecordsBtn.addEventListener("click", shareRecords);
loadDoctorsBtn.addEventListener("click", loadDoctors);

// Initialize app
window.addEventListener("load", function() {
  checkAuth();
});

















