document.addEventListener('DOMContentLoaded', function () {
  // Mobile menu
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // "Who it's for" dropdown (click / keyboard; hover handled in CSS on desktop)
  document.querySelectorAll('.nav-dropdown').forEach(function (dd) {
    var btn = dd.querySelector('.nav-dropdown-toggle');
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = dd.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    dd.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { dd.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
    });
  });
  document.addEventListener('click', function (e) {
    document.querySelectorAll('.nav-dropdown.open').forEach(function (dd) {
      if (!dd.contains(e.target)) { dd.classList.remove('open'); dd.querySelector('.nav-dropdown-toggle').setAttribute('aria-expanded', 'false'); }
    });
  });

  // ---------- Contact form ----------
  var form = document.getElementById('contact-form');
  if (!form) return;

  var params = new URLSearchParams(window.location.search);
  var segment = params.get('segment') || '';
  var typeSelect = form.querySelector('select[name="OrganisationType"]');
  var otherRow = document.getElementById('other-type-row');
  var segmentMap = {
    schools: 'School',
    membership: 'Membership or subscription charity',
    events: 'Charity running fundraising events or appeals'
  };

  // Remember which landing page the enquiry came from, so sign-ups can be counted by segment.
  var segField = form.querySelector('input[name="Segment"]');
  var srcField = form.querySelector('input[name="SourcePage"]');
  if (segField) segField.value = segment || 'general';
  if (srcField) srcField.value = params.get('from') || document.referrer || 'direct';
  if (typeSelect && segmentMap[segment]) typeSelect.value = segmentMap[segment];

  if (typeSelect && otherRow) {
    var update = function () {
      otherRow.style.display = typeSelect.value === 'Other' ? '' : 'none';
      if (segField && !segment) {
        var key = Object.keys(segmentMap).find(function (k) { return segmentMap[k] === typeSelect.value; });
        segField.value = key || 'general';
      }
    };
    typeSelect.addEventListener('change', update);
    update();
  }

  var status = document.getElementById('form-status');
  var ok = document.getElementById('form-success');
  var showSent = function () {
    form.hidden = true;
    ok.hidden = false;
    ok.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  // a form posted without JavaScript comes back here from the app
  if (params.get('sent') === '1') showSent();

  // forms sent within moments of the page opening are from bots, which the app ignores
  var loadedAt = Date.now();
  form.addEventListener('submit', function (e) {
    form.querySelector('input[name="ElapsedMs"]').value = Date.now() - loadedAt;
    if (!window.fetch) return; // old browsers: normal post
    e.preventDefault();
    var btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Sending…';
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error('bad status');
        showSent();
      })
      .catch(function () {
        status.className = 'form-errors';
        status.textContent = 'Sorry, something went wrong. Please try again or email info@donorchase.com.';
        status.hidden = false;
        btn.disabled = false;
        btn.textContent = 'Submit';
      });
  });
});
