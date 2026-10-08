// Secure Appointment Booking System Client Logic
let token = localStorage.getItem("jwt_token") || null;
let currentUser = JSON.parse(localStorage.getItem("current_user") || "null");
let selectedServiceId = null;
let selectedSlotId = null;
let reschedulingAppointmentId = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  if (token && currentUser) {
    updateNavForUser();
    showScreen("screen-booking");
    loadServices();
  } else {
    showScreen("screen-auth");
  }
});

function showAlert(message, type = "info") {
  const alertEl = document.getElementById("global-alert");
  const textEl = document.getElementById("global-alert-text");
  alertEl.className = `security-alert ${type}`;
  textEl.textContent = message;
  alertEl.style.display = "flex";
  setTimeout(() => {
    // Keep errors visible longer
    if (type !== 'error') alertEl.style.display = "none";
  }, 7000);
}

function dismissAlert() {
  document.getElementById("global-alert").style.display = "none";
}

function showScreen(screenId) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));

  const targetScreen = document.getElementById(screenId);
  if (targetScreen) targetScreen.classList.add("active");

  const navMap = {
    "screen-booking": "nav-booking",
    "screen-history": "nav-history",
    "screen-provider": "nav-provider",
    "screen-audit": "nav-audit"
  };
  if (navMap[screenId]) {
    const navBtn = document.getElementById(navMap[screenId]);
    if (navBtn) navBtn.classList.add("active");
  }

  // Load screen-specific data
  if (screenId === "screen-booking") loadServices();
  if (screenId === "screen-history") loadMyAppointments();
  if (screenId === "screen-provider") loadProviderData();
  if (screenId === "screen-audit") loadAuditData();
}

function fillCreds(email, pwd) {
  document.getElementById("login-email").value = email;
  document.getElementById("login-password").value = pwd;
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const err = await res.json();
      showAlert(err.detail || "Authentication failed", "error");
      return;
    }

    const data = await res.json();
    token = data.access_token;
    currentUser = data.user;
    localStorage.setItem("jwt_token", token);
    localStorage.setItem("current_user", JSON.stringify(currentUser));

    showAlert(`Welcome, ${currentUser.name} (${currentUser.role})`, "success");
    updateNavForUser();
    showScreen(currentUser.role === "faculty" ? "screen-provider" : "screen-booking");
  } catch (err) {
    showAlert("Network connection error: " + err.message, "error");
  }
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem("jwt_token");
  localStorage.removeItem("current_user");
  document.getElementById("main-nav").style.display = "none";
  document.getElementById("user-profile").style.display = "none";
  showScreen("screen-auth");
  showAlert("Signed out successfully.", "info");
}

function updateNavForUser() {
  if (!currentUser) return;
  document.getElementById("main-nav").style.display = "flex";
  document.getElementById("user-profile").style.display = "flex";
  document.getElementById("user-name-display").textContent = currentUser.name;
  
  const roleBadge = document.getElementById("user-role-badge");
  roleBadge.textContent = currentUser.role;
  roleBadge.className = `role-tag ${currentUser.role}`;

  // Role visibility permissions
  document.getElementById("nav-provider").style.display = (currentUser.role === "faculty" || currentUser.role === "admin") ? "block" : "none";
  document.getElementById("nav-audit").style.display = (currentUser.role === "admin") ? "block" : "none";
}

async function loadServices() {
  try {
    const res = await fetch("/api/services");
    const services = await res.json();
    const container = document.getElementById("service-list");
    container.innerHTML = "";

    const slotSelect = document.getElementById("new-slot-service");
    if (slotSelect) slotSelect.innerHTML = "";

    services.forEach((s, idx) => {
      const card = document.createElement("div");
      card.className = `service-card ${selectedServiceId === s.id ? 'selected' : ''}`;
      card.onclick = () => selectService(s.id);
      card.innerHTML = `
        <div class="service-name">${s.name}</div>
        <div class="service-desc">${s.description}</div>
        <div class="service-footer">
          <span>Duration: ${s.duration_minutes} min</span>
          <span style="color: var(--accent-primary); font-weight: 500;">Select Service →</span>
        </div>
      `;
      container.appendChild(card);

      if (slotSelect) {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        slotSelect.appendChild(opt);
      }

      if (idx === 0 && !selectedServiceId) {
        selectService(s.id);
      }
    });
  } catch (err) {
    showAlert("Failed to load services: " + err.message, "error");
  }
}

function selectService(serviceId) {
  selectedServiceId = serviceId;
  selectedSlotId = null;
  document.getElementById("btn-book-slot").disabled = true;
  document.querySelectorAll(".service-card").forEach(c => c.classList.remove("selected"));
  event?.currentTarget?.classList.add("selected");
  loadSlots(serviceId);
}

async function loadSlots(serviceId) {
  try {
    const res = await fetch(`/api/slots?service_id=${serviceId}`);
    const slots = await res.json();
    const container = document.getElementById("slots-container");
    container.innerHTML = "";

    if (slots.length === 0) {
      container.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-secondary);">No slots defined for this service.</p>`;
      return;
    }

    const grid = document.createElement("div");
    grid.className = "slots-grid";

    slots.forEach(slot => {
      const item = document.createElement("div");
      item.className = `slot-item ${slot.is_booked ? 'booked' : ''} ${selectedSlotId === slot.id ? 'selected' : ''}`;
      if (!slot.is_booked) {
        item.onclick = () => selectSlot(slot.id, item);
      }
      item.innerHTML = `
        <div class="slot-time">${slot.start_time} - ${slot.end_time}</div>
        <div style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.2rem;">${slot.slot_date}</div>
        <div class="slot-provider">${slot.provider_name}</div>
        <div style="margin-top: 0.3rem;">
          <span class="badge ${slot.is_booked ? 'badge-danger' : 'badge-success'}">${slot.is_booked ? 'Reserved' : 'Available'}</span>
        </div>
      `;
      grid.appendChild(item);
    });

    container.appendChild(grid);
  } catch (err) {
    showAlert("Failed to load slots: " + err.message, "error");
  }
}

function selectSlot(slotId, el) {
  selectedSlotId = slotId;
  document.querySelectorAll(".slot-item").forEach(i => i.classList.remove("selected"));
  el.classList.add("selected");
  document.getElementById("btn-book-slot").disabled = false;
}

async function bookSelectedSlot() {
  if (!selectedSlotId) return;
  try {
    const res = await fetch("/api/appointments/book", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ slot_id: selectedSlotId })
    });

    const data = await res.json();
    if (res.status === 201) {
      showAlert(`Appointment Confirmed! (ID: ${data.appointment_id})`, "success");
      loadSlots(selectedServiceId);
      document.getElementById("btn-book-slot").disabled = true;
      selectedSlotId = null;
    } else {
      showAlert(data.detail || "Booking failed", "error");
    }
  } catch (err) {
    showAlert("Booking request error: " + err.message, "error");
  }
}

// Concurrency Race-Condition Demonstration
async function runLiveConcurrencyTest(useVulnerable = false) {
  if (!selectedSlotId) {
    showAlert("Please select a slot first to test concurrent booking race conditions.", "error");
    return;
  }
  const targetSlot = selectedSlotId;
  const endpoint = useVulnerable ? "/api/appointments/vulnerable-book" : "/api/appointments/book";
  
  showAlert(`Launching 2 simultaneous requests against slot ${targetSlot} (${useVulnerable ? 'Vulnerable TOCTOU path' : 'Secure Atomic Lock'})...`, "info");

  // Send two requests simultaneously to prove race condition defense
  const req1 = fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    body: JSON.stringify({ slot_id: targetSlot })
  });
  const req2 = fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    body: JSON.stringify({ slot_id: targetSlot })
  });

  const [res1, res2] = await Promise.all([req1, req2]);
  const data1 = await res1.json();
  const data2 = await res2.json();

  if (useVulnerable) {
    if (res1.status === 201 && res2.status === 201) {
      showAlert(`[SECURITY FLAW REPRODUCED] Both requests returned 201 Created! Slot ${targetSlot} was DOUBLE-BOOKED. TOCTOU Race Condition confirmed!`, "error");
    } else {
      showAlert(`Req 1: ${res1.status}, Req 2: ${res2.status}`, "info");
    }
  } else {
    if ((res1.status === 201 && res2.status === 409) || (res1.status === 409 && res2.status === 201)) {
      showAlert(`[DEFENSE VERIFIED] One request succeeded (201 Created) and the second was atomically blocked (409 Conflict). Zero double bookings!`, "success");
    } else {
      showAlert(`Req 1: ${res1.status} (${data1.detail || 'ok'}), Req 2: ${res2.status} (${data2.detail || 'ok'})`, "info");
    }
  }

  loadSlots(selectedServiceId);
}

async function loadMyAppointments() {
  try {
    const res = await fetch("/api/appointments/my", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const apps = await res.json();
    const tableBody = document.getElementById("my-appointments-table");
    tableBody.innerHTML = "";

    if (apps.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No appointments found.</td></tr>`;
      return;
    }

    apps.forEach(app => {
      const tr = document.createElement("tr");
      const badgeClass = app.status === "CONFIRMED" ? "badge-success" : (app.status === "CANCELLED" ? "badge-danger" : "badge-info");
      
      let actions = "-";
      if (app.status === "CONFIRMED") {
        actions = `
          <button class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;" onclick="openRescheduleModal(${app.id})">Reschedule</button>
          <button class="btn btn-danger" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; margin-left: 0.4rem;" onclick="cancelAppointment(${app.id})">Cancel</button>
        `;
      }

      tr.innerHTML = `
        <td style="font-family: monospace;">#${app.id}</td>
        <td><strong>${app.service_name}</strong></td>
        <td>${app.provider_name}</td>
        <td>${app.slot_date} ${app.start_time} - ${app.end_time}</td>
        <td><span class="badge ${badgeClass}">${app.status}</span></td>
        <td>${actions}</td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    showAlert("Failed to load appointments: " + err.message, "error");
  }
}

async function cancelAppointment(appId) {
  if (!confirm("Are you sure you want to cancel this appointment? This action is irreversible and recorded in the audit log.")) return;
  try {
    const res = await fetch(`/api/appointments/${appId}/cancel`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await res.json();
    if (res.ok) {
      showAlert("Appointment cancelled and slot released.", "success");
      loadMyAppointments();
    } else {
      showAlert(data.detail || "Cancellation failed", "error");
    }
  } catch (err) {
    showAlert("Cancellation error: " + err.message, "error");
  }
}

async function openRescheduleModal(appId) {
  reschedulingAppointmentId = appId;
  const select = document.getElementById("reschedule-slot-select");
  select.innerHTML = "<option>Loading available slots...</option>";
  document.getElementById("reschedule-modal").classList.add("active");

  try {
    const res = await fetch("/api/slots");
    const slots = await res.json();
    const availableSlots = slots.filter(s => !s.is_booked);
    select.innerHTML = "";

    if (availableSlots.length === 0) {
      select.innerHTML = "<option disabled>No alternative slots available</option>";
      return;
    }

    availableSlots.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.slot_date} [${s.start_time} - ${s.end_time}] - ${s.service_name} (${s.provider_name})`;
      select.appendChild(opt);
    });
  } catch (err) {
    showAlert("Failed to load slots for reschedule: " + err.message, "error");
  }
}

function closeRescheduleModal() {
  document.getElementById("reschedule-modal").classList.remove("active");
  reschedulingAppointmentId = null;
}

async function confirmReschedule() {
  const newSlotId = document.getElementById("reschedule-slot-select").value;
  if (!newSlotId || !reschedulingAppointmentId) return;

  try {
    const res = await fetch(`/api/appointments/${reschedulingAppointmentId}/reschedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ new_slot_id: parseInt(newSlotId) })
    });
    const data = await res.json();
    if (res.ok) {
      showAlert("Appointment successfully rescheduled with atomic lock.", "success");
      closeRescheduleModal();
      loadMyAppointments();
    } else {
      showAlert(data.detail || "Reschedule failed", "error");
    }
  } catch (err) {
    showAlert("Reschedule error: " + err.message, "error");
  }
}

async function loadProviderData() {
  try {
    const res = await fetch("/api/provider/appointments", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const apps = await res.json();
    const tableBody = document.getElementById("provider-roster-table");
    tableBody.innerHTML = "";

    if (apps.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-secondary);">No appointments on roster.</td></tr>`;
      return;
    }

    apps.forEach(app => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family: monospace;">#${app.id}</td>
        <td><strong>${app.student_name}</strong><br><span style="font-size:0.75rem; color:var(--text-muted);">${app.student_email}</span></td>
        <td>${app.service_name}</td>
        <td>${app.slot_date} ${app.start_time} - ${app.end_time}</td>
        <td><span class="badge ${app.status === 'CONFIRMED' ? 'badge-success' : (app.status === 'COMPLETED' ? 'badge-info' : 'badge-danger')}">${app.status}</span></td>
        <td>
          <select class="form-select" style="font-size: 0.75rem; padding: 0.2rem;" onchange="updateStatus(${app.id}, this.value)">
            <option value="">Update...</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
        </td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    showAlert("Failed to load provider data: " + err.message, "error");
  }
}

async function updateStatus(appId, newStatus) {
  if (!newStatus) return;
  try {
    const res = await fetch(`/api/provider/appointments/${appId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showAlert(`Status updated to ${newStatus}`, "success");
      loadProviderData();
    } else {
      const err = await res.json();
      showAlert(err.detail || "Status update failed", "error");
    }
  } catch (err) {
    showAlert("Update error: " + err.message, "error");
  }
}

async function handleCreateSlot(e) {
  e.preventDefault();
  const service_id = parseInt(document.getElementById("new-slot-service").value);
  const slot_date = document.getElementById("new-slot-date").value;
  const start_time = document.getElementById("new-slot-start").value;
  const end_time = document.getElementById("new-slot-end").value;

  try {
    const res = await fetch("/api/slots", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ service_id, slot_date, start_time, end_time })
    });
    if (res.ok) {
      showAlert("New availability slot published successfully.", "success");
      loadSlots(service_id);
    } else {
      const err = await res.json();
      showAlert(err.detail || "Slot creation failed", "error");
    }
  } catch (err) {
    showAlert("Slot creation error: " + err.message, "error");
  }
}

async function loadAuditData() {
  try {
    const [metricsRes, logsRes] = await Promise.all([
      fetch("/api/metrics"),
      fetch("/api/audit/logs", { headers: { "Authorization": `Bearer ${token}` } })
    ]);

    if (metricsRes.ok) {
      const metrics = await metricsRes.json();
      document.getElementById("metric-conflicts").textContent = metrics.concurrency_conflicts_prevented;
      document.getElementById("metric-failed-logins").textContent = metrics.failed_logins;
      document.getElementById("metric-confirmed").textContent = metrics.confirmed_appointments;
      document.getElementById("metric-slots").textContent = metrics.available_slots;
    }

    if (logsRes.ok) {
      const logs = await logsRes.json();
      const tbody = document.getElementById("audit-logs-table");
      tbody.innerHTML = "";
      logs.forEach(log => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td style="font-size:0.75rem; color:var(--text-muted); font-family:monospace;">${log.timestamp}</td>
          <td>${log.user_name || 'Anonymous'}</td>
          <td><code>${log.action}</code></td>
          <td><span class="badge ${log.status === 'SUCCESS' || log.status === 'CONFIRMED' ? 'badge-success' : 'badge-danger'}">${log.status}</span></td>
          <td style="font-family:monospace; font-size:0.8rem;">${log.ip_address || '-'}</td>
          <td style="font-size:0.8rem;">${log.details || '-'}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    showAlert("Audit loading error: " + err.message, "error");
  }
}
