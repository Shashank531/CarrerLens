// ============================================================
// CareerLens — Unified Continuous & Random Music Player (music.js)
// ============================================================

// Complete Tracklist with timestamps (in seconds)
const CAREERLENS_TRACKLIST = [
  { time: 0,    title: "Fred again.. ft. Jozzy - Ten" },
  { time: 183,  title: "Fred again.. - Cautious (Tuesday Idea)" },
  { time: 370,  title: "Libianca - People (Fred again.. Edit)" },
  { time: 715,  title: "Fred again.. & Obongjayar - adore u" },
  { time: 993,  title: "Fred again.. - Roze (Forgive)" },
  { time: 1210, title: "Fred again.. - ID" },
  { time: 1603, title: "Jayda G - Both Of Us (Fred again.. Piano Freddit)" },
  { time: 1960, title: "Fred again.. & John Martyn - Little Mystery" },
  { time: 2325, title: "Fred again.. - Hannah (The Sun)" },
  { time: 2550, title: "Fred again.. - Cloud Tee" },
  { time: 2920, title: "Fred again.. ft. Sampha - Fear Less" },
  { time: 3150, title: "Lana Del Rey - Say Yes To Heaven (Fred again.. Freddit)" },
  { time: 3375, title: "Fred again.. & Rampa - The Longest" },
  { time: 3800, title: "Fred again.. - ID" },
  { time: 3955, title: "Fred again.. ft. Jozzy - Ten (DnB Freddit)" },
  { time: 4112, title: "Fred again.. ft. Jozzy - Ten" },
  { time: 4365, title: "Fred again.. - Hannah (The Sun) w/ Mike" },
  { time: 4570, title: "Fred again.. ft. Baxter Dury - Baxter (These Are My Friends)" },
  { time: 4860, title: "Lemon - Samaritan (Fred again.. Remix)" },
  { time: 5100, title: "Fred again.. & Duskus & Four Tet & Joy Anonymous & Skrillex - Glow" },
  { time: 5350, title: "Fred again.. - Side By Side" },
  { time: 5520, title: "Mizormac - Return Of The Mac (Fred again.. Edit)" },
  { time: 5700, title: "Fred again.. - Kyren (My Son) w/ ID" },
  { time: 5890, title: "Fred again.. & Anderson .Paak ft. CHIKA - places to be" }
];

(function() {
  const DEFAULT_VOLUME = 0.22;
  const audio = document.getElementById('bgAudio');
  const playBtn = document.getElementById('playPauseBtn');
  const prevBtn = document.getElementById('prevTrackBtn');
  const nextBtn = document.getElementById('nextTrackBtn');
  const shuffleBtn = document.getElementById('shuffleBtn');
  const volumeSlider = document.getElementById('volumeSlider');
  const muteBtn = document.getElementById('muteBtn');

  const PLAY_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
  const PAUSE_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
  const VOL_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>';
  const MUTE_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>';

  if (!audio) return;
  audio.preload = 'auto';

  let currentTrackIndex = 0;

  function findTrackIndexByTime(currentTime) {
    let idx = 0;
    for (let i = 0; i < CAREERLENS_TRACKLIST.length; i++) {
      if (currentTime >= CAREERLENS_TRACKLIST[i].time) {
        idx = i;
      } else {
        break;
      }
    }
    return idx;
  }

  // Update Now Playing UI display
  let lastRenderedTitle = "";
  function updateTrackDisplay(title) {
    if (!title) {
      const idx = findTrackIndexByTime(audio.currentTime || targetTime);
      title = CAREERLENS_TRACKLIST[idx].title;
    }
    if (title === lastRenderedTitle) return;
    lastRenderedTitle = title;

    const nowPlayingEls = document.querySelectorAll('.now-playing');
    nowPlayingEls.forEach(el => {
      el.innerHTML = `
        <span class="music-visualizer"><span class="v-bar"></span><span class="v-bar"></span><span class="v-bar"></span><span class="v-bar"></span></span>
        <strong>Now Playing:</strong> <span style="display:inline-block; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:bottom;" title="${title}">${title}</span>
      `;
    });
  }

  function setPlayingState(isPlaying) {
    const playerEl = document.querySelector('.music-player');
    if (playerEl) {
      if (isPlaying) playerEl.classList.add('is-playing');
      else playerEl.classList.remove('is-playing');
    }
  }

  function updateMuteIcon() {
    if (!muteBtn) return;
    if (audio.volume === 0 || audio.muted) {
      muteBtn.innerHTML = MUTE_ICON;
    } else {
      muteBtn.innerHTML = VOL_ICON;
    }
  }

  // --- Session & Continuous Timestamp Restoration ---
  const lastTs = parseFloat(localStorage.getItem('cl_music_last_ts')) || 0;
  const elapsed = lastTs > 0 ? (Date.now() - lastTs) / 1000 : 999999;
  const isContinuousSession = (elapsed >= 0 && elapsed < 60);

  let targetTime = 0.0;
  if (isContinuousSession) {
    const savedTime = parseFloat(localStorage.getItem('cl_music_time')) || 0.0;
    targetTime = savedTime + elapsed;
    currentTrackIndex = findTrackIndexByTime(targetTime);
  } else {
    // Random track for new session
    currentTrackIndex = Math.floor(Math.random() * CAREERLENS_TRACKLIST.length);
    targetTime = CAREERLENS_TRACKLIST[currentTrackIndex].time;
    localStorage.setItem('cl_music_time', targetTime.toString());
    localStorage.setItem('cl_music_last_ts', Date.now().toString());
    sessionStorage.removeItem('cl_user_explicit_paused');
  }

  updateTrackDisplay(CAREERLENS_TRACKLIST[currentTrackIndex].title);

  // Restore volume and mute states
  const savedVol = parseFloat(localStorage.getItem('cl_music_volume'));
  const volume = (!isNaN(savedVol) && savedVol >= 0 && savedVol <= 1) ? savedVol : DEFAULT_VOLUME;
  const savedMuted = localStorage.getItem('cl_music_muted') === 'true';

  audio.volume = volume;
  audio.muted = savedMuted;
  if (volumeSlider) volumeSlider.value = savedMuted ? 0 : volume;
  updateMuteIcon();

  let initialSeekCompleted = false;

  function applySeek() {
    if (initialSeekCompleted) return;
    if (audio.readyState >= 1) {
      try {
        let t = targetTime;
        if (audio.duration && t >= audio.duration) t = t % audio.duration;
        audio.currentTime = t;
        initialSeekCompleted = true;
        currentTrackIndex = findTrackIndexByTime(audio.currentTime);
        updateTrackDisplay(CAREERLENS_TRACKLIST[currentTrackIndex].title);
      } catch (e) {}
    }
  }

  function saveState() {
    if (!audio || !initialSeekCompleted) return;
    try {
      localStorage.setItem('cl_music_time', audio.currentTime.toString());
      localStorage.setItem('cl_music_last_ts', Date.now().toString());
      localStorage.setItem('cl_music_volume', audio.volume.toString());
      localStorage.setItem('cl_music_muted', audio.muted ? 'true' : 'false');
    } catch (e) {}
  }

  function tryPlay() {
    applySeek();
    const isUserExplicitPaused = sessionStorage.getItem('cl_user_explicit_paused') === 'true';
    if (isUserExplicitPaused) {
      if (playBtn) playBtn.innerHTML = PLAY_ICON;
      return;
    }

    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        if (playBtn) playBtn.innerHTML = PAUSE_ICON;
        updateMuteIcon();
        updateTrackDisplay();
        saveState();
      }).catch(() => {
        if (playBtn) playBtn.innerHTML = PLAY_ICON;
        armGestureUnlock();
      });
    }
  }

  function armGestureUnlock() {
    function onFirstInteraction() {
      applySeek();
      const isExplicitPaused = sessionStorage.getItem('cl_user_explicit_paused') === 'true';
      if (!isExplicitPaused && audio.paused) {
        audio.play().then(() => {
          if (playBtn) playBtn.innerHTML = PAUSE_ICON;
          updateTrackDisplay();
          saveState();
        }).catch(() => {});
      }
    }
    document.addEventListener('click', onFirstInteraction, { once: true });
    document.addEventListener('keydown', onFirstInteraction, { once: true });
    document.addEventListener('touchstart', onFirstInteraction, { once: true });
  }

  // Audio Events
  audio.addEventListener('loadedmetadata', () => {
    applySeek();
    tryPlay();
  });
  audio.addEventListener('canplay', () => {
    applySeek();
  });
  audio.addEventListener('play', () => {
    applySeek();
    if (playBtn) playBtn.innerHTML = PAUSE_ICON;
    setPlayingState(true);
    sessionStorage.removeItem('cl_user_explicit_paused');
    saveState();
  });
  audio.addEventListener('pause', () => {
    if (playBtn) playBtn.innerHTML = PLAY_ICON;
    setPlayingState(false);
  });
  audio.addEventListener('timeupdate', () => {
    if (!initialSeekCompleted && audio.readyState >= 1) {
      applySeek();
    }
    if (initialSeekCompleted) {
      const idx = findTrackIndexByTime(audio.currentTime);
      if (idx !== currentTrackIndex) {
        currentTrackIndex = idx;
        updateTrackDisplay(CAREERLENS_TRACKLIST[currentTrackIndex].title);
      }
      saveState();
    }
  });
  audio.addEventListener('volumechange', () => {
    updateMuteIcon();
    saveState();
  });

  // Jump to specific track index
  function jumpToIndex(index) {
    currentTrackIndex = (index + CAREERLENS_TRACKLIST.length) % CAREERLENS_TRACKLIST.length;
    const track = CAREERLENS_TRACKLIST[currentTrackIndex];
    targetTime = track.time;
    initialSeekCompleted = false;

    updateTrackDisplay(track.title);

    try {
      audio.currentTime = track.time;
      initialSeekCompleted = true;
    } catch(e) {}

    localStorage.setItem('cl_music_time', targetTime.toString());
    localStorage.setItem('cl_music_last_ts', Date.now().toString());
    sessionStorage.removeItem('cl_user_explicit_paused');
    saveState();

    const p = audio.play();
    if (p !== undefined) {
      p.then(() => {
        if (playBtn) playBtn.innerHTML = PAUSE_ICON;
        updateTrackDisplay(track.title);
        saveState();
      }).catch(() => {});
    }
  }

  // Play / Pause Toggle
  function togglePlayPause() {
    if (audio.paused) {
      applySeek();
      sessionStorage.removeItem('cl_user_explicit_paused');
      audio.play().then(() => {
        if (playBtn) playBtn.innerHTML = PAUSE_ICON;
        updateTrackDisplay();
        saveState();
      }).catch(() => {});
    } else {
      audio.pause();
      if (playBtn) playBtn.innerHTML = PLAY_ICON;
      sessionStorage.setItem('cl_user_explicit_paused', 'true');
    }
  }

  // Button Listeners
  if (playBtn) {
    playBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePlayPause();
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      jumpToIndex(currentTrackIndex - 1);
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      jumpToIndex(currentTrackIndex + 1);
    });
  }

  if (shuffleBtn) {
    shuffleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      let nextIdx = currentTrackIndex;
      while (nextIdx === currentTrackIndex && CAREERLENS_TRACKLIST.length > 1) {
        nextIdx = Math.floor(Math.random() * CAREERLENS_TRACKLIST.length);
      }
      jumpToIndex(nextIdx);
    });
  }

  // Volume Slider Handler
  if (volumeSlider) {
    volumeSlider.addEventListener('input', function() {
      const val = parseFloat(this.value);
      audio.volume = val;
      if (val > 0) {
        audio.muted = false;
      }
      localStorage.setItem('cl_music_volume', audio.volume.toString());
      localStorage.setItem('cl_music_muted', audio.muted.toString());
      updateMuteIcon();
      saveState();
    });
  }

  // Mute Button Handler
  if (muteBtn) {
    muteBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      audio.muted = !audio.muted;
      if (audio.muted) {
        this.innerHTML = MUTE_ICON;
      } else {
        if (audio.volume === 0) {
          audio.volume = DEFAULT_VOLUME;
          if (volumeSlider) volumeSlider.value = DEFAULT_VOLUME;
        } else {
          if (volumeSlider) volumeSlider.value = audio.volume;
        }
        this.innerHTML = VOL_ICON;
      }
      localStorage.setItem('cl_music_muted', audio.muted.toString());
      saveState();
    });
  }

  // Global Window API
  window.playNextTrack = function() { jumpToIndex(currentTrackIndex + 1); };
  window.playPrevTrack = function() { jumpToIndex(currentTrackIndex - 1); };
  window.playRandomTrack = function() {
    let nextIdx = currentTrackIndex;
    while (nextIdx === currentTrackIndex && CAREERLENS_TRACKLIST.length > 1) {
      nextIdx = Math.floor(Math.random() * CAREERLENS_TRACKLIST.length);
    }
    jumpToIndex(nextIdx);
  };
  window.jumpToTrack = function(track) {
    if (!track) return;
    const idx = CAREERLENS_TRACKLIST.findIndex(t => t.time === track.time);
    if (idx !== -1) jumpToIndex(idx);
    else {
      targetTime = track.time;
      audio.currentTime = track.time;
      audio.play().catch(() => {});
    }
  };
  window.toggleMusic = togglePlayPause;

  // Cross-tab Synchronization
  window.addEventListener('storage', function(e) {
    if (e.key === 'cl_music_volume' && e.newValue !== null) {
      const vol = parseFloat(e.newValue);
      if (!isNaN(vol)) {
        audio.volume = vol;
        if (!audio.muted && volumeSlider) volumeSlider.value = vol;
        updateMuteIcon();
      }
    }
    if (e.key === 'cl_music_muted') {
      audio.muted = e.newValue === 'true';
      updateMuteIcon();
    }
  });

  // State persistence on unload and hide
  window.addEventListener('beforeunload', saveState);
  window.addEventListener('pagehide', saveState);
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') saveState();
  });

  setInterval(saveState, 300);

  // Initialize playback immediately
  if (audio.readyState >= 1) {
    applySeek();
    tryPlay();
  } else {
    tryPlay();
  }

  window.__audio = audio;
  window.__tracklist = CAREERLENS_TRACKLIST;
})();
