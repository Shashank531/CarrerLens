/**
 * CareerLens — bg3d-control.js
 * Universal 3D Background Toggle Engine for the entire web application.
 * Persists user preference ('on' | 'off') in localStorage ('careerlens-3d-bg').
 */
(function() {
  const STORAGE_KEY = 'careerlens-3d-bg';

  function get3dState() {
    return localStorage.getItem(STORAGE_KEY) || 'on';
  }

  function set3dState(state) {
    const validState = state === 'off' ? 'off' : 'on';
    localStorage.setItem(STORAGE_KEY, validState);
    document.documentElement.setAttribute('data-3d', validState);
    updateButtons(validState);
    window.dispatchEvent(new CustomEvent('3dbgchange', { detail: { state: validState } }));
  }

  window.toggle3dBackground = function() {
    const current = get3dState();
    const next = current === 'on' ? 'off' : 'on';
    set3dState(next);
    return next;
  };

  function updateButtons(state) {
    const isOff = state === 'off';
    const btns = document.querySelectorAll('.bg3d-toggle-btn');
    btns.forEach(btn => {
      if (isOff) {
        btn.classList.add('is-off');
        btn.setAttribute('title', '3D Particle Background: OFF (Click to Enable)');
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.7;">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <line x1="2" y1="2" x2="22" y2="22" stroke="var(--rust, #C45A32)" stroke-width="2.5"/>
          </svg>
          <span>3D: OFF</span>
        `;
      } else {
        btn.classList.remove('is-off');
        btn.setAttribute('title', '3D Particle Background: ON (Click to Disable)');
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
          <span>3D: ON</span>
        `;
      }
    });
  }

  // Inject 3D button into Music Player on the left side of Previous Track button
  function attachToMusicPlayer() {
    const playerControls = document.querySelector('.music-player .player-controls');
    if (playerControls && !document.getElementById('musicPlayer3dToggle')) {
      const prevTrackBtn = document.getElementById('prevTrackBtn') || playerControls.querySelector('.track-btn, .play-btn');
      const btn = document.createElement('button');
      btn.className = 'bg3d-toggle-btn';
      btn.id = 'musicPlayer3dToggle';
      btn.setAttribute('aria-label', 'Toggle 3D Background');
      btn.setAttribute('type', 'button');
      btn.onclick = window.toggle3dBackground;
      if (prevTrackBtn && prevTrackBtn.parentNode === playerControls) {
        playerControls.insertBefore(btn, prevTrackBtn);
      } else {
        playerControls.insertBefore(btn, playerControls.firstChild);
      }
      updateButtons(get3dState());
    }
  }

  // Apply initial state right away
  const initialState = get3dState();
  document.documentElement.setAttribute('data-3d', initialState);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      attachToMusicPlayer();
      updateButtons(get3dState());
    });
  } else {
    attachToMusicPlayer();
    updateButtons(initialState);
  }
})();
