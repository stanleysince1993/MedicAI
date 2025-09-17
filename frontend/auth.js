const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const loginFormContainer = document.getElementById("loginForm");
const registerFormContainer = document.getElementById("registerForm");
const successMessage = document.getElementById("successMessage");
const loginFormElement = document.getElementById("loginFormElement");
const registerFormElement = document.getElementById("registerFormElement");

const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");

const regEmail = document.getElementById("regEmail");
const regPassword = document.getElementById("regPassword");
const regFullName = document.getElementById("regFullName");
const regUserType = document.getElementById("regUserType");
const regLicense = document.getElementById("regLicense");
const regSpecialization = document.getElementById("regSpecialization");
const regBirthDate = document.getElementById("regBirthDate");
const regPhone = document.getElementById("regPhone");

const doctorFields = document.getElementById("doctorFields");
const patientFields = document.getElementById("patientFields");

function hideElement(element) {
  if (element) {
    element.classList.add("hidden");
  }
}

function showElement(element) {
  if (element) {
    element.classList.remove("hidden");
  }
}

function showSuccess(user) {
  hideElement(loginFormContainer);
  hideElement(registerFormContainer);
  if (successMessage) {
    successMessage.classList.remove("hidden");
  }

  const welcomeText = document.getElementById("welcomeText");
  if (welcomeText && user) {
    const userTypeText = user.user_type === "doctor" ? "doctor" : "paciente";
    welcomeText.textContent = `Bienvenido, ${user.full_name}! Has iniciado sesion como ${userTypeText}.`;
  }

  localStorage.setItem("user", JSON.stringify(user));
  if (user.token) {
    localStorage.setItem("token", user.token);
  }
}

function toggleUserTypeFields(value) {
  if (!doctorFields || !patientFields) {
    return;
  }

  if (value === "doctor") {
    showElement(doctorFields);
    hideElement(patientFields);
  } else if (value === "patient") {
    showElement(patientFields);
    hideElement(doctorFields);
  } else {
    hideElement(doctorFields);
    hideElement(patientFields);
  }
}

if (regUserType) {
  toggleUserTypeFields(regUserType.value);
  regUserType.addEventListener("change", function () {
    toggleUserTypeFields(this.value);
  });
}

if (loginFormElement) {
  loginFormElement.addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = loginEmail?.value.trim();
    const password = loginPassword?.value;

    if (!email || !password) {
      alert("Por favor completa todos los campos");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        data.user.token = data.token;
        showSuccess(data.user);
        setTimeout(() => {
          window.location.href = data.user.user_type === "doctor" ? "./doctor.html" : "./patient.html";
        }, 600);
      } else {
        alert(data.detail || "Error al iniciar sesion");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      alert("Error de red: " + message);
    }
  });
}

if (registerFormElement) {
  registerFormElement.addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = regEmail?.value.trim();
    const password = regPassword?.value;
    const fullName = regFullName?.value.trim();
    const userType = regUserType?.value;

    if (!email || !password || !fullName || !userType) {
      alert("Por favor completa todos los campos requeridos");
      return;
    }

    const payload = {
      email,
      password,
      full_name: fullName,
      user_type: userType,
    };

    if (userType === "doctor") {
      payload.license_number = regLicense?.value.trim() || null;
      payload.specialization = regSpecialization?.value.trim() || null;
    }

    if (userType === "patient") {
      payload.date_of_birth = regBirthDate?.value || null;
      payload.phone = regPhone?.value.trim() || null;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        data.user.token = data.token;
        showSuccess(data.user);
        setTimeout(() => {
          window.location.href = data.user.user_type === "doctor" ? "./doctor.html" : "./patient.html";
        }, 600);
      } else {
        alert(data.detail || "Error en el registro");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      alert("Error de red: " + message);
    }
  });
}

function goToApp() {
  window.location.href = "./index.html";
}

window.goToApp = goToApp;

window.addEventListener("load", function () {
  const storedUser = localStorage.getItem("user");
  const token = localStorage.getItem("token");

  if (storedUser && token && successMessage) {
    const parsedUser = JSON.parse(storedUser);
    parsedUser.token = token;
    showSuccess(parsedUser);
  }
});
