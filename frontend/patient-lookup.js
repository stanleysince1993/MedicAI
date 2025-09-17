const API_BASE = "http://127.0.0.1:8000";

document.getElementById("lookupForm").addEventListener("submit", async function(e) {
  e.preventDefault();

  const patientCode = document.getElementById("patientCode").value.trim().toUpperCase();
  if (!patientCode) {
    alert("Ingresa el c\u00f3digo del paciente");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/patients/lookup/${patientCode}`);
    const data = await response.json();

    if (response.ok) {
      showPatientInfo(data);
    } else {
      showNotFound();
    }
  } catch (error) {
    alert("Error de red: " + error.message);
  } finally {
    setLoading(false);
  }
});

function setLoading(loading) {
  const btn = document.getElementById("lookupBtn");
  const status = document.getElementById("status");

  if (loading) {
    btn.disabled = true;
    btn.textContent = "Consultando...";
    status.textContent = "Buscando informaci\u00f3n del paciente...";
  } else {
    btn.disabled = false;
    btn.textContent = "Consultar historia";
    status.textContent = "";
  }
}

function showPatientInfo(data) {
  document.getElementById("notFound").classList.add("hidden");

  document.getElementById("patientName").textContent = data.patient.name;
  document.getElementById("patientBirthDate").textContent =
    data.patient.date_of_birth ? new Date(data.patient.date_of_birth).toLocaleDateString() : "No especificada";
  document.getElementById("patientPhone").textContent = data.patient.phone || "No especificado";
  document.getElementById("patientEmergency").textContent = data.patient.emergency_contact || "No especificado";

  displayRecords(data.records);

  document.getElementById("patientInfo").classList.remove("hidden");
}

function displayRecords(records) {
  const recordsList = document.getElementById("recordsList");

  if (!records.length) {
    recordsList.innerHTML = "<p>No se encontraron registros m\u00e9dicos.</p>";
    return;
  }

  recordsList.innerHTML = records.map(record => `
    <div class="record-card">
      <div class="record-header">
        <h3>Consulta del ${new Date(record.created_at).toLocaleDateString()}</h3>
        <span class="record-time">${new Date(record.created_at).toLocaleTimeString()}</span>
      </div>

      ${record.reason_for_visit ? `
        <div class="record-section">
          <h4>Motivo de consulta</h4>
          <p>${record.reason_for_visit}</p>
        </div>
      ` : ''}

      ${record.vital_signs ? `
        <div class="record-section">
          <h4>Signos vitales</h4>
          <div class="vital-signs-display">
            ${record.vital_signs.heart_rate ? `<span>FC: ${record.vital_signs.heart_rate} lpm</span>` : ''}
            ${record.vital_signs.blood_pressure_systolic && record.vital_signs.blood_pressure_diastolic ?
              `<span>PA: ${record.vital_signs.blood_pressure_systolic}/${record.vital_signs.blood_pressure_diastolic} mmHg</span>` : ''}
            ${record.vital_signs.temperature ? `<span>Temp.: ${record.vital_signs.temperature} \u00b0C</span>` : ''}
            ${record.vital_signs.oxygen_saturation ? `<span>SpO2: ${record.vital_signs.oxygen_saturation}%</span>` : ''}
            ${record.vital_signs.weight && record.vital_signs.height ?
              `<span>Peso: ${record.vital_signs.weight} kg, Estatura: ${record.vital_signs.height} cm</span>` : ''}
            ${record.vital_signs.bmi ? `<span>IMC: ${record.vital_signs.bmi}</span>` : ''}
          </div>
        </div>
      ` : ''}

      ${record.allergies && record.allergies.length ? `
        <div class="record-section">
          <h4>Alergias</h4>
          <p>${record.allergies.join(', ')}</p>
        </div>
      ` : ''}

      ${record.current_medications && record.current_medications.length ? `
        <div class="record-section">
          <h4>Medicamentos actuales</h4>
          <p>${record.current_medications.join(', ')}</p>
        </div>
      ` : ''}

      ${record.physical_examination ? `
        <div class="record-section">
          <h4>Examen f\u00edsico</h4>
          <p>${record.physical_examination}</p>
        </div>
      ` : ''}

      ${record.assessment ? `
        <div class="record-section">
          <h4>Evaluaci\u00f3n</h4>
          <p>${record.assessment}</p>
        </div>
      ` : ''}

      ${record.diagnosis ? `
        <div class="record-section">
          <h4>Diagn\u00f3stico</h4>
          <p>${record.diagnosis}</p>
        </div>
      ` : ''}

      ${record.treatment_plan ? `
        <div class="record-section">
          <h4>Plan de tratamiento</h4>
          <p>${record.treatment_plan}</p>
        </div>
      ` : ''}

      ${record.follow_up ? `
        <div class="record-section">
          <h4>Seguimiento</h4>
          <p>${record.follow_up}</p>
        </div>
      ` : ''}

      ${record.differentials && record.differentials.length ? `
        <div class="record-section">
          <h4>Diagn\u00f3sticos diferenciales</h4>
          <ul>
            ${record.differentials.map(diff => `<li>${diff.condition}: ${diff.probability || ''}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${record.tests && record.tests.length ? `
        <div class="record-section">
          <h4>Pruebas sugeridas</h4>
          <ul>
            ${record.tests.map(test => `<li>${test.test}: ${test.reason || ''}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    </div>
  `).join('');
}

function showNotFound() {
  document.getElementById("patientInfo").classList.add("hidden");
  document.getElementById("notFound").classList.remove("hidden");
}

function resetLookup() {
  document.getElementById("lookupForm").reset();
  document.getElementById("patientInfo").classList.add("hidden");
  document.getElementById("notFound").classList.add("hidden");
}

document.getElementById("patientCode").addEventListener("input", function(e) {
  e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
});
