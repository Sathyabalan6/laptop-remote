// ─────────────────────────────────────────────────────────────────
//  APPLICATION ENTRYPOINT, PIN PAIRING OVERLAY & PWA REGISTRATION
// ─────────────────────────────────────────────────────────────────
function showPinOverlay() {
  const pinOverlay = document.getElementById('pinOverlay');
  const hiddenInput = document.getElementById('pinInputHidden');
  const pinBoxes = document.querySelectorAll('.pin-box');
  if (pinBoxes && pinBoxes.length > 0) {
    pinBoxes.forEach(b => b.classList.remove('active-caret'));
    pinBoxes[0].classList.add('active-caret');
  }
  if (typeof setBackgroundInert === 'function') setBackgroundInert(true);
  if (pinOverlay) {
    pinOverlay.style.display = 'flex';
    void pinOverlay.offsetWidth;
    pinOverlay.classList.add('visible');
  }
  if (hiddenInput) {
    setTimeout(() => hiddenInput.focus(), 50);
  }
}

function hidePinOverlay() {
  const pinOverlay = document.getElementById('pinOverlay');
  const hiddenInput = document.getElementById('pinInputHidden');
  if (typeof setBackgroundInert === 'function') setBackgroundInert(false);
  if (pinOverlay) {
    pinOverlay.classList.remove('visible');
    setTimeout(() => {
      if (!pinOverlay.classList.contains('visible')) {
        pinOverlay.style.display = 'none';
      }
    }, 280);
  }
  if (hiddenInput) hiddenInput.blur();
}

async function submitPin(pin) {
  try {
    const r = await fetch('/pair', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin })
    });
    const data = await r.json();
    if (r.ok) {
      localStorage.setItem('session_token', data.token);
      hidePinOverlay();
      showToast('🔑 Successfully paired!');
      connectSocket(data.token);
      return { ok: true };
    }
    return { ok: false, error: data.error || 'Invalid Pairing PIN' };
  } catch (e) {
    return { ok: false, error: 'Connection failed' };
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const pinOverlay = document.getElementById('pinOverlay');
  const hiddenInput = document.getElementById('pinInputHidden');
  const pinBoxes = document.querySelectorAll('.pin-box');
  const pinError = document.getElementById('pinError');
  const wifiHelp = document.getElementById('wifiHelpCard');

  if (pinOverlay && hiddenInput) {
    pinOverlay.addEventListener('click', () => {
      hiddenInput.focus();
    });

    hiddenInput.addEventListener('input', async e => {
      const val = e.target.value.replace(/\D/g, '').slice(0, 6);
      e.target.value = val;
      
      pinBoxes.forEach((box, idx) => {
        box.textContent = val[idx] || '';
        box.classList.toggle('filled', !!val[idx]);
        box.classList.toggle('active-caret', idx === (val.length < 6 ? val.length : -1));
      });
      
      if (pinError) pinError.classList.remove('visible');
      
      if (val.length === 6) {
        hiddenInput.blur();
        vibrate(20);
        const res = await submitPin(val);
        if (!res.ok) {
          if (wifiHelp) wifiHelp.classList.remove('hidden');
          if (pinError) {
            pinError.textContent = res.error;
            pinError.classList.add('visible');
          }
          vibrate([40, 40, 40]);
          setTimeout(() => {
            hiddenInput.value = '';
            pinBoxes.forEach((box, idx) => {
              box.textContent = '';
              box.classList.remove('filled');
              box.classList.toggle('active-caret', idx === 0);
            });
            if (res.error && res.error.indexOf('locked') === -1) {
              hiddenInput.focus();
            }
          }, 500);
        }
      }
    });
  }

  const searchInput = document.getElementById('searchInput');
  const searchClearBtn = document.getElementById('searchClearBtn');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      if (searchClearBtn) {
        searchClearBtn.classList.toggle('visible', searchInput.value.length > 0);
      }
      handleLiveTyping(searchInput);
    });
    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitSearch(true);
      }
    });
    // Tapping anywhere in the search box (padding / icon area) should focus the
    // input so the on-screen keyboard opens reliably.
    const searchWrapper = searchInput.closest('.search-input-wrapper');
    if (searchWrapper) {
      searchWrapper.addEventListener('click', () => {
        if (document.activeElement !== searchInput) searchInput.focus();
      });
    }
  }

  // Initialize socket & preset UI state
  setPreset(currentPreset, true);
  connectSocket(localStorage.getItem('session_token') || '');
  if (typeof io === 'undefined') setInterval(checkConnection, 15000);

  // Register PWA service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {});
  }
});
