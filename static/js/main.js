var currentStep = 1;
var currentCar  = {};

function openBooking(id, name, category, rate, icon) {
  currentCar = {id, name, category, rate, icon};
  currentStep = 1;
  document.getElementById('fleet_id').value = id;
  document.getElementById('modal-heading').textContent = 'Reserve — ' + name;
  document.getElementById('modal-car-info').innerHTML =
    '<div class="modal-car-icon">' + icon + '</div>' +
    '<div><div class="modal-car-name">' + name + '</div>' +
    '<div class="modal-car-price">$' + rate + ' / day</div></div>';
  showStep(1);
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function showStep(n) {
  [1, 2, 3].forEach(function(i) {
    var el = document.getElementById('mstep' + i);
    if (el) el.style.display = i === n ? 'block' : 'none';
    var tab = document.getElementById('tab' + i);
    if (tab) tab.className = 'step-tab' + (i === n ? ' active' : i < n ? ' done' : '');
  });
  var footer = document.getElementById('modal-footer');
  if (n === 3) {
    buildFeeBox();
    footer.innerHTML =
      '<button type="button" class="btn-modal-cancel" onclick="prevStep()">← Back</button>' +
      '<button type="submit" form="booking-form" class="btn-modal-primary">Submit request</button>';
  } else {
    footer.innerHTML =
      '<button type="button" class="btn-modal-cancel" onclick="' + (n === 1 ? 'closeModal()' : 'prevStep()') + '">' + (n === 1 ? 'Cancel' : '← Back') + '</button>' +
      '<button type="button" class="btn-modal-primary" onclick="nextStep()">Next →</button>';
  }
}

function nextStep() {
  if (currentStep < 3) { currentStep++; showStep(currentStep); }
}

function prevStep() {
  if (currentStep > 1) { currentStep--; showStep(currentStep); }
}

function buildFeeBox() {
  var p1   = document.getElementById('m-pickup').value;
  var p2   = document.getElementById('m-return').value;
  var days = 1;
  if (p1 && p2) {
    var diff = Math.round((new Date(p2) - new Date(p1)) / 86400000);
    days = Math.max(1, diff);
  }
  var sub   = currentCar.rate * days;
  var fee   = 15;
  var total = sub + fee;
  document.getElementById('fee-box').innerHTML =
    '<div class="fee-row"><span>' + currentCar.name + ' × ' + days + ' day' + (days > 1 ? 's' : '') + '</span><span>$' + sub.toFixed(2) + '</span></div>' +
    '<div class="fee-row"><span>Location fee</span><span>$' + fee.toFixed(2) + '</span></div>' +
    '<div class="fee-row"><span>Insurance (included)</span><span>$0.00</span></div>' +
    '<div class="fee-row total"><span>Total (on approval)</span><span>$' + total.toFixed(2) + '</span></div>';
}

function filterFleet() {
  var type = document.getElementById('s-type').value.toLowerCase();
  document.querySelectorAll('.car-card').forEach(function(card) {
    var t = (card.dataset.type || '').toLowerCase();
    card.classList.toggle('hidden', type !== '' && t !== type);
  });
}

document.addEventListener('click', function(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});
