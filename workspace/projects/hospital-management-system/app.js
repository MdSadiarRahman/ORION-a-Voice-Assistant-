// Interactive Client Script for VoiceMate Scaffolded Web App
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

  const targetPane = document.getElementById('tab-' + tabId);
  if (targetPane) {
    targetPane.classList.add('active');
  }

  // Set active sidebar button
  event.currentTarget.classList.add('active');
}

function bookAppointment(e) {
  e.preventDefault();
  const name = document.getElementById('p-name').value;
  const phone = document.getElementById('p-phone').value;
  const dept = document.getElementById('p-dept').value;

  if (!name || !phone) return;

  const appt = { name, phone, dept, time: new Date().toLocaleTimeString() };
  let appointments = JSON.parse(localStorage.getItem('appointments') || '[]');
  appointments.push(appt);
  localStorage.setItem('appointments', JSON.stringify(appointments));

  document.getElementById('booking-success').style.display = 'block';
  document.getElementById('appointment-form').reset();

  // Update Doctor queue dynamically
  const queue = document.getElementById('doctor-queue');
  if (queue) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>সিরিয়াল #${appointments.length + 2}:</strong> ${name} (${dept}) - অনলাইন বুকিং`;
    queue.appendChild(li);
  }
}
