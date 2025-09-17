const API_BASE = "http://127.0.0.1:8000";

// Check authentication on page load
document.addEventListener("DOMContentLoaded", function() {
  checkAuth();
});

async function checkAuth() {
  const token = localStorage.getItem("token");
  if (!token) {
    showAuthWarning();
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!response.ok) {
      showAuthWarning();
      return;
    }

    const user = await response.json();
    if (user.user_type !== "doctor") {
      showAuthWarning();
      return;
    }

    showRegistrationApp(user);
  } catch (error) {
    console.error("Auth check failed:", error);
    showAuthWarning();
  }
}

function showAuthWarning() {
  document.getElementById("authWarning").classList.remove("hidden");
  document.getElementById("registrationApp").classList.add("hidden");
}

function showRegistrationApp(user) {
  document.getElementById("authWarning").classList.add("hidden");
  document.getElementById("registrationApp").classList.remove("hidden");
  document.getElementById("userName").textContent = `Dr. ${user.full_name}`;
}

// Form submission
document.getElementById("patientRegistrationForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  
  setLoading(true);
  
  try {
    const formData = collectFormData();
    const response = await fetch(`${API_BASE}/patients/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`
      },
      body: JSON.stringify(formData)
    });

    const result = await response.json();
    
    if (response.ok) {
      showSuccess(result);
    } else {
      alert("Error: " + (result.detail || "Error al registrar paciente"));
    }
  } catch (error) {
    alert("Error de red: " + error.message);
  } finally {
    setLoading(false);
  }
});

function collectFormData() {
  const vitalSigns = {
    heart_rate: getNumberValue("heartRate"),
    blood_pressure_systolic: getNumberValue("bpSystolic"),
    blood_pressure_diastolic: getNumberValue("bpDiastolic"),
    respiratory_rate: getNumberValue("respiratoryRate"),
    temperature: getNumberValue("temperature"),
    oxygen_saturation: getNumberValue("oxygenSaturation"),
    weight: getNumberValue("weight"),
    height: getNumberValue("height"),
    blood_glucose: getNumberValue("bloodGlucose"),
    waist_circumference: getNumberValue("waistCircumference"),
    pain_scale: getNumberValue("painScale")
  };

  return {
    full_name: document.getElementById("fullName").value.trim(),
    date_of_birth: document.getElementById("dateOfBirth").value,
    phone: document.getElementById("phone").value.trim() || null,
    emergency_contact: document.getElementById("emergencyContact").value.trim() || null,
    vital_signs: vitalSigns,
    allergies: splitCommaSeparated("allergies"),
    current_medications: splitCommaSeparated("currentMedications"),
    past_history: document.getElementById("pastHistory").value.trim() || null,
    family_history: document.getElementById("familyHistory").value.trim() || null,
    reason_for_visit: document.getElementById("reasonForVisit").value.trim() || null,
    physical_examination: document.getElementById("physicalExamination").value.trim() || null,
    assessment: document.getElementById("assessment").value.trim() || null,
    diagnosis: document.getElementById("diagnosis").value.trim() || null,
    treatment_plan: document.getElementById("treatmentPlan").value.trim() || null,
    follow_up: document.getElementById("followUp").value.trim() || null
  };
}

function getNumberValue(id) {
  const value = document.getElementById(id).value;
  return value ? parseFloat(value) : null;
}

function splitCommaSeparated(id) {
  const value = document.getElementById(id).value.trim();
  if (!value) return null;
  return value.split(",").map(item => item.trim()).filter(item => item);
}

function setLoading(loading) {
  const btn = document.getElementById("registerBtn");
  const status = document.getElementById("status");
  
  if (loading) {
    btn.disabled = true;
    btn.textContent = "Registrando...";
    status.textContent = "Procesando datos del paciente...";
  } else {
    btn.disabled = false;
    btn.textContent = "Registrar Paciente";
    status.textContent = "";
  }
}

function showSuccess(result) {
  document.getElementById("patientRegistrationForm").classList.add("hidden");
  document.getElementById("successMessage").classList.remove("hidden");
  
  document.getElementById("patientName").textContent = result.patient_name;
  document.getElementById("patientCode").textContent = result.patient_code;
}

function resetForm() {
  document.getElementById("patientRegistrationForm").reset();
  document.getElementById("patientRegistrationForm").classList.remove("hidden");
  document.getElementById("successMessage").classList.add("hidden");
}

// Logout functionality
document.getElementById("logoutBtn").addEventListener("click", function() {
  localStorage.removeItem("token");
  window.location.href = "./login.html";
});

