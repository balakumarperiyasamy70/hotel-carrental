function showTab(name, el) {
  document.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.snav').forEach(function(n) { n.classList.remove('active'); });
  document.getElementById('tab-' + name).classList.add('active');
  el.classList.add('active');
}

function filterBookings(status, btn) {
  document.querySelectorAll('.fbtn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('.brow').forEach(function(row) {
    row.style.display = (status === 'all' || row.dataset.status === status) ? '' : 'none';
  });
}

function searchBookings(val) {
  val = val.toLowerCase();
  document.querySelectorAll('.brow').forEach(function(row) {
    row.style.display = row.dataset.search.includes(val) ? '' : 'none';
  });
}

function openAction(id, type, ref, name) {
  var modal = document.getElementById('action-modal');
  var form  = document.getElementById('action-form');
  var title = document.getElementById('action-title');
  var desc  = document.getElementById('action-desc');
  var btn   = document.getElementById('action-submit-btn');
  form.action = '/admin/booking/' + id + '/' + type;
  if (type === 'approve') {
    title.textContent = 'Approve booking';
    desc.textContent  = 'You are approving ' + ref + ' for ' + name + '. An optional note will be sent to the customer.';
    btn.textContent   = 'Confirm approval';
    btn.style.background = '#3B6D11';
  } else {
    title.textContent = 'Decline booking';
    desc.textContent  = 'You are declining ' + ref + ' for ' + name + '. Please provide a reason for the customer.';
    btn.textContent   = 'Confirm decline';
    btn.style.background = '#A32D2D';
  }
  modal.classList.add('open');
}

function closeActionModal() {
  document.getElementById('action-modal').classList.remove('open');
}

document.addEventListener('click', function(e) {
  if (e.target === document.getElementById('action-modal')) closeActionModal();
});
